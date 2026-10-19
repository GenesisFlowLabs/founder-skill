import json
import contextlib
import io
import os
import shutil
import tempfile
import unittest

from _load import load, example

panel = load("founder-consumer", "panel")


def customer():
    with open(example("founder-consumer", "customer.example.json"), encoding="utf-8") as fh:
        return json.load(fh)


def b2b_customer():
    return {
        "type": "b2b", "business": "Synthetic workflow tool", "target": "Small operations teams",
        "segments": [{"name": "Owner-led office", "share": 1, "roles": ["Owner", "Office manager"],
                      "organization_budget": [100, 400], "budget_period": "monthly",
                      "organization_size": [3, 12], "authority": "Owner approves the purchase",
                      "workflow_constraints": ["Keep existing scheduling"],
                      "switching_constraints": ["Export existing records before switching"]}],
        "behaviours": [{"name": "Cautious evaluator"}], "objections": ["Migration takes time"],
    }


class Deal(unittest.TestCase):
    def test_same_seed_same_cards(self):
        self.assertEqual(panel.deal(customer(), 20, 7), panel.deal(customer(), 20, 7))
        self.assertNotEqual(panel.deal(customer(), 20, 7), panel.deal(customer(), 20, 8))

    def test_quotas_are_exact_and_names_unique(self):
        cards = panel.deal(customer(), 20, 3)
        segs = {}
        for c in cards:
            segs[c["segment"]] = segs.get(c["segment"], 0) + 1
        self.assertEqual(segs, {"Early-career professional": 9, "Mid-career professional": 8, "High earner": 3})
        self.assertEqual(len({c["name"] for c in cards}), 20)
        self.assertEqual(cards[0]["id"], "P001")
        self.assertEqual(cards[-1]["id"], "P020")
        for c in cards:
            seg = next(s for s in customer()["segments"] if s["name"] == c["segment"])
            self.assertTrue(seg["income"][0] - 500 <= c["income"] <= seg["income"][1] + 500)
            self.assertIn(c["objection"], customer()["objections"])

    def test_bad_profile_is_refused(self):
        c = customer()
        del c["objections"]
        with self.assertRaises(panel.PanelError):
            panel.deal(c)

    def test_default_panel_is_small_and_invalid_counts_are_refused(self):
        self.assertEqual(len(panel.deal(customer())), 12)
        for n in (0, -1, 21, True, 1.5):
            with self.subTest(n=n), self.assertRaises(panel.PanelError):
                panel.deal(customer(), n)

    def test_invalid_profile_ranges_and_shares_are_refused(self):
        for key, value in (("income", [100, 0]), ("income", [0, float("inf")]),
                           ("income", [True, 100]), ("share", -1), ("share", float("nan"))):
            c = customer()
            c["segments"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(panel.PanelError):
                panel.deal(c)

    def test_b2b_cards_use_organizational_budget_and_roles(self):
        cards = panel.deal(b2b_customer(), 12, 7)
        self.assertEqual(len(cards), 12)
        for c in cards:
            self.assertNotIn("income", c)
            self.assertIn(c["role"], ("Owner", "Office manager"))
            self.assertTrue(100 <= c["organization_budget"] <= 400)
            self.assertTrue(3 <= c["organization_size"] <= 12)
            self.assertEqual(c["authority"], "Owner approves the purchase")
            self.assertEqual(c["budget_period"], "monthly")

    def test_b2b_profile_requires_purchasing_context(self):
        for key in ("roles", "organization_budget", "organization_size", "budget_period", "authority",
                    "workflow_constraints", "switching_constraints"):
            c = b2b_customer()
            del c["segments"][0][key]
            with self.subTest(key=key), self.assertRaises(panel.PanelError):
                panel.deal(c)


class Flow(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        panel.init(self.d, example("founder-consumer", "customer.example.json"),
                   example("founder-consumer", "pitch.example.md"), n=20, seed=5)

    def tearDown(self):
        shutil.rmtree(self.d)

    def answer(self, pid, buys, code="price", **extra):
        a = {"id": pid, "buys": buys, "reason_code": code, "reason": "because %s" % pid,
             "purchases_first_month": 4 if buys else 0, "would_change_my_mind": "" if buys else "a lower price"}
        a.update(extra)
        with open(os.path.join(self.d, "answers", pid + ".json"), "w") as fh:
            json.dump(a, fh)

    def test_briefs_carry_the_card_and_the_pitch(self):
        waves = panel.write_briefs(self.d, wave=2)
        self.assertEqual([len(w) for w in waves], [2] * 10)
        with open(waves[0][0][1], encoding="utf-8") as fh:
            brief = fh.read()
        self.assertIn("Moss Matcha Bar", brief)
        self.assertIn('"id": "P001"', brief)
        self.assertIn("Do not be agreeable", brief)

    def test_answered_buyers_get_no_new_brief(self):
        self.answer("P001", True, "quality")
        ids = [j[0] for w in panel.write_briefs(self.d) for j in w]
        self.assertNotIn("P001", ids)
        self.assertEqual(len(ids), 19)

    def test_check_and_tally(self):
        for i in range(1, 21):
            pid = "P%03d" % i
            self.answer(pid, i <= 8, "quality" if i <= 8 else ("price" if i <= 15 else "habit"))
        # one broken answer: wrong reason code
        self.answer("P020", False, "vibes")
        probs = dict(panel.check(self.d))
        self.assertEqual(list(probs), ["P020"])
        res = panel.tally(self.d)
        self.assertEqual((res["buys"], res["passes"], res["answered"]), (8, 11, 19))
        self.assertEqual(res["why_not"][0][0], "price")
        self.assertEqual(res["why_not"][0][1], 7)
        self.assertEqual(res["skipped"][0][0], "P020")
        text = panel.results_md(res)
        self.assertIn("**8 buy · 11 pass**", text)
        self.assertIn("not customers", text)

    def test_save_files_a_printed_answer_and_refuses_junk(self):
        reply = 'Here is my answer:\n```json\n{"id": "P002", "buys": false, "reason_code": "price", "reason": "too much"}\n```'
        panel.save(self.d, "P002", reply)
        self.assertNotIn("P002", dict(panel.check(self.d)))
        with self.assertRaises(panel.PanelError):
            panel.save(self.d, "P003", '{"id": "P003", "buys": "maybe", "reason_code": "price", "reason": "x"}')
        self.assertEqual(dict(panel.check(self.d))["P003"], "missing")
        with self.assertRaises(panel.PanelError):
            panel.save(self.d, "P999", '{"id": "P999"}')

    def test_tally_with_no_answers_refuses(self):
        with self.assertRaises(panel.PanelError):
            panel.tally(self.d)

    def snapshot(self):
        files = {}
        for root, _, names in os.walk(self.d):
            for name in names:
                path = os.path.join(root, name)
                with open(path, "rb") as fh:
                    files[os.path.relpath(path, self.d)] = (fh.read(), os.stat(path).st_mtime_ns)
        return files

    def test_changed_input_refuses_without_touching_existing_run(self):
        panel.write_briefs(self.d)
        self.answer("P001", True)
        original = self.snapshot()
        with tempfile.TemporaryDirectory() as inputs:
            cp, pp = os.path.join(inputs, "customer.json"), os.path.join(inputs, "pitch.md")
            with open(example("founder-consumer", "pitch.example.md"), encoding="utf-8") as fh:
                pitch = fh.read()
            for change in ("pitch", "customer", "seed", "count"):
                c = customer()
                if change == "customer":
                    c["target"] = "A different target"
                with open(cp, "w", encoding="utf-8") as fh:
                    json.dump(c, fh)
                with open(pp, "w", encoding="utf-8") as fh:
                    fh.write(pitch + ("\nChanged offer" if change == "pitch" else ""))
                with self.subTest(change=change):
                    with self.assertRaisesRegex(panel.PanelError, "new.*directory"):
                        panel.init(self.d, cp, pp, n=19 if change == "count" else 20,
                                   seed=6 if change == "seed" else 5)
                    self.assertEqual(self.snapshot(), original)

    def test_identical_init_resumes_without_rewriting_and_reuses_seed(self):
        self.answer("P001", True)
        original = self.snapshot()
        for seed in (5, None):
            cards = panel.init(self.d, example("founder-consumer", "customer.example.json"),
                               example("founder-consumer", "pitch.example.md"), n=20, seed=seed)
            self.assertEqual(len(cards), 20)
            self.assertEqual(self.snapshot(), original)
            self.assertNotIn("P001", dict(panel.check(self.d)))

    def test_partial_existing_run_is_not_overwritten(self):
        os.remove(os.path.join(self.d, "panel.json"))
        original = self.snapshot()
        with self.assertRaises(panel.PanelError):
            panel.init(self.d, example("founder-consumer", "customer.example.json"),
                       example("founder-consumer", "pitch.example.md"), n=20, seed=5)
        self.assertEqual(self.snapshot(), original)

    def test_waves_are_bounded_before_any_brief_is_written(self):
        original = self.snapshot()
        for wave in (0, -1, 3, True, 1.5):
            with self.subTest(wave=wave), self.assertRaises(panel.PanelError):
                panel.write_briefs(self.d, wave=wave)
            self.assertEqual(self.snapshot(), original)
        self.assertTrue(all(len(w) <= 2 for w in panel.write_briefs(self.d)))

    def test_cli_default_initializes_twelve_buyers(self):
        with tempfile.TemporaryDirectory() as run, contextlib.redirect_stdout(io.StringIO()):
            code = panel.main(["--dir", run, "init", "--customer",
                               example("founder-consumer", "customer.example.json"), "--pitch",
                               example("founder-consumer", "pitch.example.md")])
            self.assertEqual(code, 0)
            self.assertEqual(len(panel.load_state(run)[1]), 12)

    def test_b2b_briefs_carry_organizational_purchasing_constraints(self):
        with tempfile.TemporaryDirectory() as run, tempfile.TemporaryDirectory() as inputs:
            cp = os.path.join(inputs, "customer.json")
            with open(cp, "w", encoding="utf-8") as fh:
                json.dump(b2b_customer(), fh)
            panel.init(run, cp, example("founder-consumer", "pitch.example.md"), n=2, seed=7)
            waves = panel.write_briefs(run)
            with open(waves[0][0][1], encoding="utf-8") as fh:
                brief = fh.read()
            for text in ("Organizational budget", "monthly", "Owner approves the purchase",
                         "Keep existing scheduling", "Export existing records before switching"):
                self.assertIn(text, brief)
            self.assertNotIn("You earn", brief)
            self.assertNotIn("'s money", brief)

    def test_b2b_example_completes_tally_without_personal_income_labels(self):
        with tempfile.TemporaryDirectory() as run:
            panel.init(run, example("founder-consumer", "customer.b2b.example.json"),
                       example("founder-consumer", "pitch.example.md"), n=2, seed=7)
            for pid, buys in (("P001", True), ("P002", False)):
                panel.save(run, pid, json.dumps({"id": pid, "buys": buys,
                                                "reason_code": "need", "reason": "synthetic fixture"}))
            res = panel.tally(run)
            self.assertEqual((res["buys"], res["passes"]), (1, 1))
            self.assertTrue(res["by_role"])
            self.assertEqual(res["by_income"], [])
            text = panel.results_md(res)
            self.assertIn("By purchasing role", text)
            self.assertIn("By organizational budget", text)
            self.assertNotIn("By income", text)


if __name__ == "__main__":
    unittest.main()
