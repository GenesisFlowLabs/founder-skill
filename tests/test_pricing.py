import csv
import contextlib
import io
import json
import subprocess
import sys
import os
import tempfile
import unittest

from _load import load

vw = load("founder-pricing", "van_westendorp")


def rows(n=40):
    out = []
    for i in range(n):
        k = i / float(n - 1)
        out.append((2.5 + k, 4.0 + k, 6.0 + 1.5 * k, 7.5 + 2 * k))
    return out


class Pricing(unittest.TestCase):
    def test_points_are_ordered_and_inside_the_answers(self):
        res = vw.analyse(rows())
        p = res["points"]
        for k in ("PMC", "PME", "OPP", "IPP"):
            self.assertIsNotNone(p[k], k)
            self.assertTrue(2.5 <= p[k] <= 9.5, (k, p[k]))
        self.assertLess(p["PMC"], p["PME"])
        self.assertLessEqual(p["PMC"], p["OPP"])
        self.assertLessEqual(p["OPP"], p["PME"])

    def test_fractional_span_includes_upper_endpoint_for_crossing(self):
        # A 4.0 span / 0.01 is represented just below 400 in binary floats.
        res = vw.analyse([(0.1, 1.0, 4.1, 4.1)] * 5)
        self.assertIsNotNone(res["points"]["PME"])
        self.assertAlmostEqual(res["points"]["PME"], 4.095, places=10)

    def test_custom_steps_include_exact_unrounded_upper_endpoint(self):
        for hi, step, expected in ((4.1, 0.3, 4.05), (4.10001, 0.3, 4.050005),
                                   (4.1, 10, 2.1)):
            with self.subTest(hi=hi, step=step):
                res = vw.analyse([(0.1, 1.0, hi, hi)] * 5, step=step)
                self.assertIsNotNone(res["points"]["PME"])
                self.assertAlmostEqual(res["points"]["PME"], expected, places=10)

    def test_endpoint_counts_toward_bounded_grid_before_allocation(self):
        # 9,999 whole intervals plus the exact endpoint fit 10,000 points.
        res = vw.analyse([(1, 2, 10000, 10000)] * 5, step=1)
        self.assertAlmostEqual(res["points"]["PME"], 9999.5)
        # A fractional last interval requires an additional endpoint beyond the cap.
        for hi in (10000.5, 10001):
            with self.subTest(hi=hi), self.assertRaises(vw.PricingError):
                vw.analyse([(1, 2, hi, hi)] * 5, step=1)

    def test_out_of_order_and_incomplete_rows_are_dropped(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "p.csv")
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(vw.KEYS)
            for r in rows(10):
                w.writerow(r)
            w.writerow((9, 4, 6, 8))       # too cheap above a bargain: out of order
            w.writerow((3, "", 6, 8))      # incomplete
        got, dropped = vw.read(path)
        self.assertEqual((len(got), dropped), (10, 2))

    def test_too_few_answers_is_refused(self):
        with self.assertRaises(vw.PricingError):
            vw.analyse(rows(4))

    def test_report_places_the_price(self):
        res = vw.analyse(rows())
        self.assertIn("**inside** the acceptable range", vw.report(res, 0, price=6.5))
        self.assertIn("**above** the acceptable range", vw.report(res, 0, price=40))

    def test_nonfinite_and_boolean_prices_are_dropped(self):
        with tempfile.TemporaryDirectory() as d:
            for i, value in enumerate((float("inf"), float("nan"), True, -2, 0)):
                with open(os.path.join(d, str(i) + ".json"), "w") as fh:
                    json.dump(dict(zip(("price_" + k for k in vw.KEYS), (1, 2, 3, value))), fh)
            got, dropped = vw.read(d)
            self.assertEqual((got, dropped), ([], 5))

    def test_analyse_rejects_invalid_direct_inputs(self):
        for bad in ((True, 2, 3, 4), (1, 3, 2, 4),
                    (0, 2, 3, 4), (1, 2, 3), ("1", 2, 3, 4), None):
            with self.subTest(bad=bad), self.assertRaises(vw.PricingError):
                vw.analyse([bad] * 5)

    def test_nonfinite_upper_bound_is_refused_without_unbounded_grid(self):
        code = ("import sys; sys.path.insert(0, 'tests'); from _load import load; "
                "vw = load('founder-pricing', 'van_westendorp')\n"
                "try: vw.analyse([(1, 2, 3, float('inf'))] * 5)\n"
                "except vw.PricingError: sys.exit(0)\n"
                "sys.exit(1)\n")
        try:
            result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=1,
                                    cwd=os.path.dirname(os.path.dirname(__file__)))
        except subprocess.TimeoutExpired:
            self.fail("nonfinite price upper bound did not terminate within one second")
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_nonfinite_or_zero_step_is_refused(self):
        for step in (float("inf"), float("nan"), 0, True):
            with self.subTest(step=step), self.assertRaises(vw.PricingError):
                vw.analyse(rows(), step=step)

    def test_unknown_source_is_not_labeled_simulated(self):
        text = vw.report(vw.analyse(rows()), 0)
        self.assertIn("Provenance: unknown", text)
        self.assertNotIn("Simulated buyers:", text)

    def test_explicit_provenance_survives_cli_json_and_report(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "p.csv")
            with open(path, "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(vw.KEYS)
                w.writerows(rows(10))
            for provenance in ("real-survey", "simulated", "unknown"):
                out = io.StringIO()
                with self.subTest(provenance=provenance), contextlib.redirect_stdout(out):
                    self.assertEqual(vw.main([path, "--json", "--provenance", provenance]), 0)
                    self.assertEqual(json.loads(out.getvalue())["provenance"], provenance)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(vw.main([path, "--provenance", "real-survey"]), 0)
            self.assertIn("Provenance: real-survey", out.getvalue())
            self.assertNotIn("Simulated buyers:", out.getvalue())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(vw.main([path, "--price", "inf"]), 2)


if __name__ == "__main__":
    unittest.main()
