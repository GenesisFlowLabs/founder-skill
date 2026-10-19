#!/usr/bin/env python3
"""Compiles the business plan for founder-plan. Standard library only, no network.

Reads everything the other ten skills wrote into founder/ and assembles one
document, founder/business-plan.md, with a verdict at the top. The verdict is
computed from the numbers, never written by hand:

    Projected profitable   the supplied financial projection passes every check
    Not yet      at least one check fails (each failure is listed with its number)
    Incomplete   required financial inputs are missing or invalid

The checks:
    1. each unit earns money before fixed costs        (founder/numbers.json)
    2. year 1 makes an operating profit                 (founder/numbers.json)
    3. break-even fits inside capacity, if capacity is given
    4. planned and month-by-month volume fit inside capacity, if given

Buyer panel results are reported separately. Simulations do not validate demand
or affect the financial verdict. --min-buy-rate is retained as a deprecated no-op.

    python3 compile.py                      # reads ./founder, writes ./founder/business-plan.md
    python3 compile.py --dir path/to/founder --min-buy-rate 0.3
    python3 compile.py --check              # print the verdict and exit 0 (Projected profitable) or 1
"""

import argparse
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SECTIONS = [  # (file in founder/, heading, which skill writes it)
    ("summary.md", "Summary", "founder-plan"),
    ("board.md", "What the board said", "founder-board"),
    ("competitors.md", "The competition", "founder-competitors"),
    ("panel/results.md", "The buyer panel", "founder-consumer"),
    ("pricing.md", "Pricing", "founder-pricing"),
    ("offer.md", "The offer", "founder-offer"),
    ("cfo.md", "The numbers", "founder-cfo"),
    ("marketing.md", "Marketing", "founder-marketing"),
    ("brand.md", "Brand", "founder-brand"),
    ("ops.md", "Operations", "founder-ops"),
    ("launch.md", "Launch plan", "founder-launch"),
]


def _load_unit_economics():
    path = os.path.join(HERE, "..", "founder-cfo", "unit_economics.py")
    spec = importlib.util.spec_from_file_location("founder_unit_economics", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except FileNotFoundError:
        return None


def _strip_h1(text):
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    # demote headings one level so they nest under the section heading
    return "\n".join(("#" + l) if l.startswith("#") else l for l in lines).strip()


def _panel(d):
    raw = _read(os.path.join(d, "panel", "results.json"))
    if raw is None:
        return None
    try:
        panel = json.loads(raw)
        if not isinstance(panel, dict):
            raise ValueError("expected an object")
        for key in ("buys", "passes", "answered"):
            value = panel.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("%s must be a nonnegative integer" % key)
        rate = panel.get("buy_rate")
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not 0 <= rate <= 1:
            raise ValueError("buy_rate must be a finite fraction between zero and one")
        if panel["buys"] + panel["passes"] != panel["answered"]:
            raise ValueError("buyer counts do not add up")
        expected = panel["buys"] / panel["answered"] if panel["answered"] else 0
        if not math.isclose(rate, expected, abs_tol=1e-9):
            raise ValueError("buy_rate does not match the buyer counts")
        return panel
    except (ValueError, OverflowError) as exc:
        return {"error": "panel/results.json unavailable: %s" % exc}


def verdict(d, min_buy_rate=0.25):
    """Return (verdict, financial_checks, numbers, panel).

    min_buy_rate is a deprecated compatibility parameter and has no effect.
    Invalid panel data returns a panel dict with an error diagnostic.
    """
    checks = []
    numbers = None
    raw = _read(os.path.join(d, "numbers.json"))
    if raw:
        ue = _load_unit_economics()
        try:
            numbers = ue.analyse(json.loads(raw))
        except (json.JSONDecodeError, ue.NumbersError) as exc:
            checks.append((False, "numbers.json is incomplete or invalid: %s" % exc))
    else:
        checks.append((False, "numbers.json is missing or empty."))
    if numbers is not None:
        u = numbers["unit"]
        c = numbers["contribution"]
        checks.append((c > 0, "Projected contribution per %s: $%.2f before fixed costs (%.0f%%)." %
                       (u, c, numbers["contribution_pct"] * 100)))
        y = numbers["year1_profit"]
        checks.append((y > 0, "Projected year 1 operating %s: $%s." %
                       ("profit" if y > 0 else "loss", "{:,.0f}".format(abs(y)))))
        be, cap = numbers["breakeven_per_day"], numbers["capacity_per_day"]
        if cap is not None:
            fits = not math.isinf(be) and be <= cap
            checks.append((fits, "Break-even is %s %ss a day against a capacity of %s." % (
                "never reached" if math.isinf(be) else "{:,.0f}".format(math.ceil(be)), u, cap)))
            peak = max([numbers["plan_per_day"]] + [month["per_day"] for month in numbers["months"]])
            checks.append((peak <= cap, "Peak projected volume is %s %ss a day against a capacity of %s." %
                           ("{:,.0f}".format(peak), u, cap)))
    panel = _panel(d)
    if numbers is None:
        v = "Incomplete"
    elif all(ok for ok, _ in checks):
        v = "Projected profitable"
    else:
        v = "Not yet"
    return v, checks, numbers, panel


def compile_plan(d, min_buy_rate=0.25):
    idea = _read(os.path.join(d, "idea.md"))
    name = None
    if idea:
        first = idea.splitlines()[0]
        name = first[2:].strip() if first.startswith("# ") else None
    v, checks, numbers, panel = verdict(d, min_buy_rate)
    title = name or (numbers["business"] if numbers and numbers.get("business") else "Your business")
    L = ["# %s · Business plan" % title, ""]
    L.append("**Verdict: %s**" % v)
    L.append("")
    for ok, text in checks:
        L.append("- %s %s" % ("✓" if ok else "✗", text))
    if v == "Incomplete":
        L.append("- Complete and verify the inputs, run /founder-cfo, then compile again.")
    L.append("")
    if numbers:
        be = numbers["breakeven_per_day"]
        margin = numbers["margin_at_plan"]
        margin_text = "undefined (no planned sales)" if margin is None else "%.0f%% per %s" % (margin * 100, numbers["unit"])
        L += ["| key number | |", "| --- | ---: |",
              "| Price | $%.2f a %s |" % (numbers["price"], numbers["unit"]),
              "| Profit margin at plan | %s |" % margin_text,
              "| Break-even | %s %ss a day |" % ("never" if math.isinf(be) else "{:,.0f}".format(math.ceil(be)), numbers["unit"]),
              "| Year 1 operating profit | $%s |" % "{:,.0f}".format(numbers["year1_profit"]),
              "| Startup spend | $%s |" % "{:,.0f}".format(numbers["startup"]),
              "| Cash needed before it pays for itself | $%s |" % "{:,.0f}".format(numbers["cash_needed"]),
              "| Startup money earned back | %s |" % ("month %d" % numbers["payback_month"] if numbers["payback_month"] else "not in year 1")]
        L.append("")
    if panel is not None:
        L += ["## Simulated buyer exercise", ""]
        if "error" in panel:
            L.append(panel["error"])
        else:
            L.append("%d of %d simulated buyers buy (%.0f%%): %d buy · %d pass." %
                     (panel["buys"], panel["answered"], panel["buy_rate"] * 100,
                      panel["buys"], panel["passes"]))
        L += ["", "This simulation does not validate demand and does not affect the financial verdict.", ""]
    if idea:
        L += ["## The idea", "", _strip_h1(idea), ""]
    missing = []
    for fname, heading, skill in SECTIONS:
        text = _read(os.path.join(d, fname))
        if text:
            L += ["## %s" % heading, "", _strip_h1(text), ""]
        else:
            missing.append((heading, skill))
    if missing:
        L += ["## Not done yet", ""]
        for heading, skill in missing:
            L.append("- %s: run /%s" % (heading, skill))
        L.append("")
    L.append("_The panel is simulated buyers and the numbers are projections from your inputs. Confirm demand with real"
             " customers and costs with real quotes before you spend. Not financial, legal or tax advice._")
    return v, "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", default="founder")
    ap.add_argument("--min-buy-rate", type=float, default=0.25, help="deprecated compatibility option; no effect on the verdict")
    ap.add_argument("--check", action="store_true", help="print the verdict only; exit 0 if Projected profitable")
    ap.add_argument("--out", help="default: <dir>/business-plan.md")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dir):
        print("error: no %s/ folder here. Run the other founder skills first." % a.dir, file=sys.stderr)
        return 2
    v, text = compile_plan(a.dir, a.min_buy_rate)
    if a.check:
        _, checks, _, _ = verdict(a.dir, a.min_buy_rate)
        print("Verdict: %s" % v)
        for ok, t in checks:
            print("  %s %s" % ("✓" if ok else "✗", t))
        return 0 if v == "Projected profitable" else 1
    out = a.out or os.path.join(a.dir, "business-plan.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("Verdict: %s. Wrote %s" % (v, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
