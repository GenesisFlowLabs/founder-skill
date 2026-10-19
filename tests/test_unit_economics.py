import contextlib
import io
import json
import os
import tempfile
import math
import unittest

from _load import load, example

ue = load("founder-cfo", "unit_economics")


def spec():
    with open(example("founder-cfo", "example.json"), encoding="utf-8") as fh:
        return json.load(fh)


class UnitEconomics(unittest.TestCase):
    def test_example_reproduces_the_plan(self):
        a = ue.analyse(spec())
        self.assertAlmostEqual(a["contribution"], 4.76, places=2)
        self.assertEqual(round(a["margin_at_plan"] * 100), 38)
        self.assertEqual(math.ceil(a["breakeven_per_day"]), 186)
        self.assertEqual(round(a["year1_profit"]), 93926)
        self.assertEqual(a["startup"], 25280)
        self.assertEqual(a["payback_month"], 8)
        self.assertEqual(round(a["cash_needed"]), 34092)
        self.assertEqual(a["flags"], [])

    def test_price_below_variable_cost_is_flagged(self):
        s = spec()
        s["price"] = 1.50
        a = ue.analyse(s)
        self.assertTrue(math.isinf(a["breakeven_per_day"]))
        self.assertTrue(any("loses money" in f for f in a["flags"]))

    def test_breakeven_above_capacity_is_flagged(self):
        s = spec()
        s["capacity_per_day"] = 150
        a = ue.analyse(s)
        self.assertTrue(any("capacity is 150" in f for f in a["flags"]))

    def test_what_ifs_move_the_right_way(self):
        base = ue.analyse(spec())
        cheaper = ue.analyse(spec(), price=base["price"] * 0.9)
        fewer = ue.analyse(spec(), volume=0.8)
        self.assertLess(cheaper["year1_profit"], base["year1_profit"])
        self.assertGreater(cheaper["breakeven_per_day"], base["breakeven_per_day"])
        self.assertLess(fewer["year1_profit"], base["year1_profit"])
        self.assertEqual(len(ue.sensitivity(spec())), 4)

    def test_bad_input_is_refused_not_guessed(self):
        s = spec()
        s["ramp_per_day"] = [100] * 11
        with self.assertRaises(ue.NumbersError):
            ue.analyse(s)
        s = spec()
        del s["price"]
        with self.assertRaises(ue.NumbersError):
            ue.analyse(s)
        s = spec()
        s["variable"][0]["cost"] = "lots"
        with self.assertRaises(ue.NumbersError):
            ue.analyse(s)

    def test_each_cost_array_is_required_even_when_others_are_present(self):
        for field in ("variable", "fixed_monthly", "startup"):
            with self.subTest(field=field):
                s = spec()
                del s[field]
                with self.assertRaisesRegex(ue.NumbersError, field):
                    ue.analyse(s)

    def test_explicit_empty_cost_arrays_confirm_zero(self):
        a = ue.analyse({"price": 10, "variable": [], "fixed_monthly": [],
                        "startup": [], "plan_per_day": 2, "days_per_month": 1})
        self.assertEqual(a["year1_profit"], 240)
        self.assertEqual(a["cash_needed"], 0)
        self.assertEqual(a["breakeven_per_day"], 0)

    def test_cost_arrays_and_items_require_proper_nonnegative_numbers(self):
        for field in ("variable", "fixed_monthly", "startup"):
            for value in (None, {}, "", [{"cost": -1}], [{"cost": True}],
                          [{"cost": "2"}], [{"cost": float("nan")}],
                          [{"cost": float("inf")}], [{}], [None]):
                with self.subTest(field=field, value=value):
                    s = spec()
                    s[field] = value
                    with self.assertRaisesRegex(ue.NumbersError, field):
                        ue.analyse(s)

    def test_model_inputs_require_finite_numbers_and_valid_ranges(self):
        for field in ("price", "days_per_month", "plan_per_day", "capacity_per_day"):
            for value in (None, True, "3", -1, float("nan"), float("inf"), 10**400):
                with self.subTest(field=field, value=value):
                    s = spec()
                    s[field] = value
                    with self.assertRaises(ue.NumbersError):
                        ue.analyse(s)
        for field in ("price", "days_per_month"):
            with self.subTest(field=field, value=0):
                s = spec()
                s[field] = 0
                with self.assertRaises(ue.NumbersError):
                    ue.analyse(s)

    def test_ramp_requires_an_array_of_twelve_nonnegative_numbers(self):
        for value in (None, 12, "1" * 12, {str(i): 1 for i in range(12)},
                      [1] * 11, [1] * 11 + [False], [1] * 11 + [-1],
                      [1] * 11 + ["2"], [1] * 11 + [float("inf")]):
            with self.subTest(value=value):
                s = spec()
                s["ramp_per_day"] = value
                with self.assertRaisesRegex(ue.NumbersError, "ramp_per_day"):
                    ue.analyse(s)

    def test_top_level_input_must_be_an_object(self):
        for value in (None, [], 1, "price"):
            with self.subTest(value=value):
                with self.assertRaises(ue.NumbersError):
                    ue.analyse(value)

    def test_what_if_overrides_are_validated_before_multiplication(self):
        for value in (True, "2", -1, float("inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaises(ue.NumbersError):
                    ue.analyse(spec(), volume=value)
                with self.assertRaises(ue.NumbersError):
                    ue.analyse(spec(), price=value)

    def test_explicit_zero_plan_is_not_replaced_by_ramp(self):
        s = spec()
        s["plan_per_day"] = 0
        a = ue.analyse(s)
        self.assertEqual(a["plan_per_day"], 0)
        self.assertIsNone(a["margin_at_plan"])
        self.assertIn("undefined", ue.report(s, a).lower())

    def test_ramp_above_capacity_is_flagged(self):
        s = spec()
        s["ramp_per_day"][0] = 601
        self.assertTrue(any("month 1" in flag.lower() and "capacity" in flag
                            for flag in ue.analyse(s)["flags"]))

    def test_finite_inputs_cannot_overflow_into_profit(self):
        s = spec()
        s["price"] = 1e308
        with self.assertRaises(ue.NumbersError):
            ue.analyse(s)

    def test_cli_invalid_input_returns_diagnostic_without_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "numbers.json")
            s = spec()
            s["plan_per_day"] = "unknown"
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(s, fh)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = ue.main([path, "--volume", "0.8"])
            self.assertEqual(code, 2)
            self.assertIn("plan_per_day", stderr.getvalue())

    def test_cli_json_zero_volume_has_no_nonstandard_numbers(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "numbers.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(spec(), fh)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = ue.main([path, "--volume", "0", "--json"])
            self.assertEqual(code, 0)
            def reject_constant(value):
                self.fail("Nonstandard JSON number: " + value)
            result = json.loads(stdout.getvalue(), parse_constant=reject_constant)
            self.assertEqual(result["year1_revenue"], 0)
            self.assertIsNone(result["margin_at_plan"])

    def test_report_mentions_the_key_numbers(self):
        s = spec()
        text = ue.report(s, ue.analyse(s))
        for needle in ("$4.76", "186 cups a day", "**38%**", "$93,926", "month 8"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
