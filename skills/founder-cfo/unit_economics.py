#!/usr/bin/env python3
"""Unit economics for founder-cfo. Standard library only, no network.

Takes one JSON file describing the business and prints the numbers a CFO would
check before a single dollar is spent: what one unit earns, the real margin at
the volume you plan, how many units a day you need to break even, what year 1
looks like month by month, and how long it takes to earn the startup money back.

    python3 unit_economics.py founder/numbers.json
    python3 unit_economics.py founder/numbers.json --out founder/cfo.md
    python3 unit_economics.py founder/numbers.json --json
    python3 unit_economics.py founder/numbers.json --price 7.00 --volume 0.8

The input (see example.json in this folder):

    business          name, for the report
    unit              what you sell one of: "cup", "order", "client-month"
    price             price per unit, before tax
    variable          [{label, cost}]  cost of ONE unit: ingredients, packaging,
                      shipping, card fees, a per-unit commission
    fixed_monthly     [{label, cost}]  costs you pay every month whatever you sell:
                      rent, salaries, software, insurance
    startup           [{label, cost}]  one-off spend before you open
                      All three cost arrays are required; [] confirms zero.
    days_per_month    selling days in a month (default 30); use 1 for monthly units
    capacity_per_day  the most units a day you can physically sell (optional)
    plan_per_day      the volume you plan for once you are up and running
    ramp_per_day      12 numbers: units a day in each month of year 1
                      (optional; default = plan_per_day every month)

Every number in the report comes from that file. Nothing is looked up or
guessed. If a field is missing the tool says so instead of filling it in.

--price and --volume run a what-if without editing the file: --price replaces
the price, --volume scales every volume (0.8 = 20 percent fewer sales).
"""

import argparse
import json
import math
import sys


class NumbersError(Exception):
    pass


def _money(v):
    sign = "-" if v < 0 else ""
    return "%s$%s" % (sign, "{:,.2f}".format(abs(v)))


def _whole(v):
    sign = "-" if v < 0 else ""
    return "%s$%s" % (sign, "{:,.0f}".format(abs(round(v))))


def _number(value, field, positive=False):
    """Accept JSON numbers only, with explicit range and finite checks."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NumbersError("%s must be a number, not %r" % (field, value))
    try:
        value = float(value)
    except OverflowError:
        raise NumbersError("%s must be finite" % field)
    if not math.isfinite(value):
        raise NumbersError("%s must be finite" % field)
    if value < 0 or (positive and value == 0):
        raise NumbersError("%s must be %s" % (field, "above zero" if positive else "nonnegative"))
    return value


def _sum(items, field):
    if not isinstance(items, list):
        raise NumbersError("%s must be an explicit array; use [] only for confirmed zero costs" % field)
    total = 0.0
    for i, it in enumerate(items):
        if not isinstance(it, dict) or "cost" not in it:
            raise NumbersError("%s[%d] needs a 'cost'" % (field, i))
        total += _number(it["cost"], "%s[%d].cost" % (field, i))
    if not math.isfinite(total):
        raise NumbersError("%s total must be finite" % field)
    return total


def _finite(value, field):
    if not math.isfinite(value):
        raise NumbersError("%s exceeds the finite range of this projection; reduce the input scale" % field)
    return value


def _percent(value):
    return "undefined (no planned sales)" if value is None else "%.0f%%" % (value * 100)


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise NumbersError("no such file: %s" % path)
    except json.JSONDecodeError as e:
        raise NumbersError("%s is not valid JSON: %s" % (path, e))


def analyse(spec, price=None, volume=1.0):
    """Return a dict of every number in the report. Pure function, easy to test."""
    if not isinstance(spec, dict):
        raise NumbersError("numbers.json must contain an object")
    if "price" not in spec and price is None:
        raise NumbersError("'price' is missing")
    p = _number(price if price is not None else spec["price"], "price", positive=True)
    days = _number(spec.get("days_per_month", 30), "days_per_month", positive=True)
    volume = _number(volume, "volume")
    for field in ("variable", "fixed_monthly", "startup"):
        if field not in spec:
            raise NumbersError("'%s' is missing; give an array, or [] for confirmed zero costs" % field)
    var = _sum(spec["variable"], "variable")
    fixed = _sum(spec["fixed_monthly"], "fixed_monthly")
    startup = _sum(spec["startup"], "startup")
    capacity = (_number(spec["capacity_per_day"], "capacity_per_day")
                if "capacity_per_day" in spec else None)

    if "plan_per_day" not in spec and "ramp_per_day" not in spec:
        raise NumbersError("give 'plan_per_day' or 'ramp_per_day' (12 numbers)")
    plan = (_finite(_number(spec["plan_per_day"], "plan_per_day") * volume, "plan_per_day")
            if "plan_per_day" in spec else None)
    if "ramp_per_day" not in spec:
        ramp = [plan] * 12
    else:
        ramp = spec["ramp_per_day"]
        if not isinstance(ramp, list) or len(ramp) != 12:
            raise NumbersError("'ramp_per_day' needs an array of 12 numbers, one per month")
        ramp = [_finite(_number(v, "ramp_per_day[%d]" % i) * volume, "ramp_per_day[%d]" % i)
                for i, v in enumerate(ramp)]
    if plan is None:
        plan = ramp[-1]

    contribution = p - var
    contribution_pct = _finite(contribution / p, "contribution percentage")
    # Divide in stages to avoid an overflowing intermediate contribution * days.
    breakeven_day = (math.inf if contribution <= 0 else
                     _finite(fixed / contribution / days, "break-even"))
    plan_units_month = _finite(plan * days, "planned monthly units")
    margin_at_plan = (None if plan_units_month == 0 else
                      _finite((contribution - fixed / plan_units_month) / p, "margin at plan"))

    months = []
    cumulative = -startup
    payback_month = None
    for m, per_day in enumerate(ramp, start=1):
        units = _finite(per_day * days, "month %d units" % m)
        revenue = _finite(units * p, "month %d revenue" % m)
        variable_cost = _finite(units * var, "month %d variable costs" % m)
        profit = _finite(revenue - variable_cost - fixed, "month %d profit" % m)
        cumulative = _finite(cumulative + profit, "month %d cumulative cash" % m)
        if payback_month is None and cumulative >= 0:
            payback_month = m
        months.append({"month": m, "per_day": per_day, "units": units, "revenue": revenue,
                       "variable": variable_cost, "fixed": fixed, "profit": profit,
                       "cumulative": cumulative})
    year_profit = _finite(sum(m["profit"] for m in months), "year 1 profit")
    year_revenue = _finite(sum(m["revenue"] for m in months), "year 1 revenue")
    after_startup = _finite(year_profit - startup, "year 1 after startup")
    # the cash you need: startup plus the deepest hole the monthly losses dig
    lowest = min([-startup] + [m["cumulative"] for m in months])
    cash_needed = -lowest

    flags = []
    if contribution <= 0:
        flags.append("Each unit loses money before rent and salaries: the price is below the variable cost.")
    if capacity is not None and breakeven_day > float(capacity):
        flags.append("Break-even needs %.0f %ss a day but capacity is %s." % (breakeven_day, spec.get("unit", "unit"), capacity))
    if capacity is not None and plan > float(capacity):
        flags.append("The plan (%.0f a day) is above capacity (%s)." % (plan, capacity))
    if capacity is not None:
        for month in months:
            if month["per_day"] > capacity:
                flags.append("Month %d volume (%.0f a day) is above capacity (%s)." %
                             (month["month"], month["per_day"], capacity))
    if year_profit < 0:
        flags.append("Year 1 loses money on operations (%s)." % _whole(year_profit))
    if payback_month is None:
        flags.append("The startup spend is not earned back within year 1.")

    return {
        "business": spec.get("business", ""), "unit": spec.get("unit", "unit"),
        "price": p, "variable_per_unit": var, "contribution": contribution,
        "contribution_pct": contribution_pct, "fixed_monthly": fixed, "startup": startup,
        "plan_per_day": plan, "margin_at_plan": margin_at_plan, "breakeven_per_day": breakeven_day,
        "capacity_per_day": capacity, "year1_revenue": year_revenue, "year1_profit": year_profit,
        "year1_after_startup": after_startup, "payback_month": payback_month,
        "cash_needed": cash_needed, "months": months, "flags": flags,
        "variable_items": spec.get("variable", []), "fixed_items": spec.get("fixed_monthly", []),
        "startup_items": spec.get("startup", []),
    }


def sensitivity(spec):
    """The three what-ifs every plan should survive."""
    base = analyse(spec)
    rows = [("Base plan", base)]
    rows.append(("Price -10%", analyse(spec, price=base["price"] * 0.9)))
    rows.append(("Volume -20%", analyse(spec, volume=0.8)))
    worse = json.loads(json.dumps(spec))
    for it in worse.get("variable", []):
        it["cost"] = float(it["cost"]) * 1.15
    rows.append(("Unit costs +15%", analyse(worse)))
    return rows


def report(spec, a):
    u = a["unit"]
    L = []
    L.append("# Unit economics: %s" % (a["business"] or "your business"))
    L.append("")
    L.append("These are projections from the supplied assumptions and documented defaults, not proof of profitability or demand.")
    L.append("")
    L.append("## One %s" % u)
    L.append("")
    L.append("| line | per %s |" % u)
    L.append("| --- | ---: |")
    L.append("| Price | %s |" % _money(a["price"]))
    for it in a["variable_items"]:
        L.append("| %s | -%s |" % (it.get("label", "cost"), _money(float(it["cost"]))))
    L.append("| **Contribution** (what each %s leaves to pay the fixed costs) | **%s** (%.0f%%) |"
             % (u, _money(a["contribution"]), a["contribution_pct"] * 100))
    L.append("")
    L.append("## The margin that matters")
    L.append("")
    L.append("Fixed costs: %s a month (%s)." % (_whole(a["fixed_monthly"]), ", ".join(
        "%s %s" % (it.get("label", "cost"), _whole(float(it["cost"]))) for it in a["fixed_items"]) or "confirmed zero"))
    L.append("")
    be = a["breakeven_per_day"]
    L.append("- **Break-even: %s %ss a day.** Below that you lose money every month." % (
        "never (each unit loses money)" if math.isinf(be) else "{:,.0f}".format(math.ceil(be)), u))
    L.append("- **Profit margin at your plan** (%s a day): **%s** of every sale, after the supplied costs." % (
        "{:,.0f}".format(a["plan_per_day"]), _percent(a["margin_at_plan"])))
    if a["capacity_per_day"] is not None:
        L.append("- Capacity: %s a day." % a["capacity_per_day"])
    L.append("")
    L.append("## Year 1, month by month")
    L.append("")
    L.append("| month | %ss a day | revenue | profit | cumulative (after %s startup) |" % (u, _whole(a["startup"])))
    L.append("| ---: | ---: | ---: | ---: | ---: |")
    for m in a["months"]:
        L.append("| %d | %s | %s | %s | %s |" % (m["month"], "{:,.0f}".format(m["per_day"]), _whole(m["revenue"]),
                                             _whole(m["profit"]), _whole(m["cumulative"])))
    L.append("")
    L.append("- **Year 1 operating profit: %s** on %s of revenue." % (_whole(a["year1_profit"]), _whole(a["year1_revenue"])))
    L.append("- After the %s startup spend: %s." % (_whole(a["startup"]), _whole(a["year1_after_startup"])))
    L.append("- Startup money earned back: %s." % ("month %d" % a["payback_month"] if a["payback_month"] else "not within year 1"))
    L.append("- Cash you need before it pays for itself: **%s**." % _whole(a["cash_needed"]))
    L.append("")
    L.append("## What if")
    L.append("")
    L.append("| scenario | margin at plan | break-even a day | year 1 profit |")
    L.append("| --- | ---: | ---: | ---: |")
    for name, s in sensitivity(spec):
        be = s["breakeven_per_day"]
        L.append("| %s | %s | %s | %s |" % (name, _percent(s["margin_at_plan"]),
                                              "never" if math.isinf(be) else "{:,.0f}".format(math.ceil(be)),
                                              _whole(s["year1_profit"])))
    L.append("")
    if a["flags"]:
        L.append("## Red flags")
        L.append("")
        for f in a["flags"]:
            L.append("- %s" % f)
    else:
        L.append("No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("numbers", help="the business's numbers.json")
    ap.add_argument("--out", help="write the report here (markdown)")
    ap.add_argument("--json", action="store_true", help="print the numbers as JSON")
    ap.add_argument("--price", type=float, help="what-if price")
    ap.add_argument("--volume", type=float, default=1.0, help="what-if volume multiplier")
    args = ap.parse_args(argv)
    try:
        spec = load(args.numbers)
        a = analyse(spec, price=args.price, volume=args.volume)
        # Sensitivity rows must start from the same effective scenario as the report.
        spec = dict(spec, price=a["price"], plan_per_day=a["plan_per_day"],
                    ramp_per_day=[month["per_day"] for month in a["months"]])
        text = None if args.json else report(spec, a)
    except NumbersError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    if args.json:
        out = {k: v for k, v in a.items() if not k.endswith("_items")}
        out["breakeven_per_day"] = None if math.isinf(out["breakeven_per_day"]) else out["breakeven_per_day"]
        print(json.dumps(out, indent=1, allow_nan=False))
        return 0
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s" % args.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
