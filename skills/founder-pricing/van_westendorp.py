#!/usr/bin/env python3
"""Price sensitivity (Van Westendorp) for founder-pricing. Standard library only.

Every buyer on the panel answers four questions: at what price would it be too
cheap to trust, a bargain, getting expensive, and too expensive to buy. Plotted
together, those four answers give you an acceptable price range and the price
that leaves the fewest people unhappy.

    python3 van_westendorp.py founder/panel/answers --provenance simulated
    python3 van_westendorp.py prices.csv --provenance real-survey --out founder/pricing-curve.md
    python3 van_westendorp.py founder/panel/answers --provenance simulated --json

Input is either the panel's answers folder (one JSON per buyer, written by
founder-consumer) or a CSV with the columns too_cheap, cheap, expensive,
too_expensive (one row per respondent; extra columns are ignored). A respondent
missing any of the four numbers, or giving them out of order (too cheap must be
the lowest, too expensive the highest), is dropped and counted.

The four points it reports:

    PMC  point of marginal cheapness   below this, too many think it's too cheap
    PME  point of marginal expensiveness above this, too many think it's too expensive
    OPP  optimal price point            as many say "too cheap" as "too expensive"
    IPP  indifference price point       as many say "a bargain" as "expensive"

PMC to PME is a stated acceptable range, not purchase evidence. Select
--provenance simulated, real-survey, or unknown (the conservative default).
Simulated answers only suggest what to test with actual customers.
"""

import argparse
import csv
import glob
import json
import math
import os
import sys

KEYS = ("too_cheap", "cheap", "expensive", "too_expensive")
PROVENANCES = ("simulated", "real-survey", "unknown")
MAX_GRID = 10000


class PricingError(Exception):
    pass


def _f(v):
    if isinstance(v, bool):
        return None
    try:
        x = float(str(v).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and x > 0 else None


def _positive(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    try:
        return math.isfinite(v) and v > 0
    except OverflowError:
        return False


def read(path):
    """Return (rows, dropped) where rows are (too_cheap, cheap, expensive, too_expensive)."""
    raw = []
    if os.path.isdir(path):
        for fp in sorted(glob.glob(os.path.join(path, "*.json"))):
            try:
                with open(fp, encoding="utf-8") as fh:
                    a = json.load(fh)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raw.append(None)
                continue
            raw.append(tuple(_f(a.get("price_" + k)) for k in KEYS) if isinstance(a, dict) else None)
    elif path.endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                raw.append(tuple(_f(r.get(k)) for k in KEYS))
    else:
        raise PricingError("give the panel's answers folder or a .csv")
    rows, dropped = [], 0
    for r in raw:
        if r is None or any(v is None for v in r) or not (r[0] <= r[1] <= r[2] <= r[3]):
            dropped += 1
            continue
        rows.append(r)
    return rows, dropped


def curves(rows, grid):
    n = float(len(rows))
    tc = [sum(1 for r in rows if r[0] >= p) / n for p in grid]          # too cheap at p (falls)
    ch = [sum(1 for r in rows if r[1] >= p) / n for p in grid]          # a bargain at p (falls)
    ex = [sum(1 for r in rows if r[2] <= p) / n for p in grid]          # expensive at p (rises)
    te = [sum(1 for r in rows if r[3] <= p) / n for p in grid]          # too expensive at p (rises)
    return tc, ch, ex, te


def cross(grid, falling, rising):
    """First price where the rising curve meets the falling one (linear interpolation)."""
    for i in range(1, len(grid)):
        d0 = rising[i - 1] - falling[i - 1]
        d1 = rising[i] - falling[i]
        if d0 <= 0 <= d1 and d1 != d0:
            t = -d0 / (d1 - d0)
            return grid[i - 1] + t * (grid[i] - grid[i - 1])
        if d0 == 0:
            return grid[i - 1]
    return None


def analyse(rows, step=None):
    if not isinstance(rows, (list, tuple)):
        raise PricingError("answers must be a list of four-price rows")
    for row in rows:
        if (not isinstance(row, (list, tuple)) or len(row) != 4
                or not all(_positive(v) for v in row)
                or not row[0] <= row[1] <= row[2] <= row[3]):
            raise PricingError("each answer needs four finite positive numbers in ascending order")
    if len(rows) < 5:
        raise PricingError("need at least 5 complete answers (got %d)" % len(rows))
    lo = min(r[0] for r in rows)
    hi = max(r[3] for r in rows)
    if step is None:
        step = max(0.01, round((hi - lo) / 400, 2))
    if not _positive(step):
        raise PricingError("step must be a finite positive number")
    intervals = (hi - lo) / step
    if not math.isfinite(intervals):
        raise PricingError("step would exceed %d price grid points; use a larger step" % MAX_GRID)
    # Normalize floating error at an integral number of intervals, then count
    # the exact upper endpoint before allocating. Nonintegral spans need a
    # final shorter interval; omitting it can hide a crossing at the top price.
    nearest = round(intervals)
    if math.isclose(intervals, nearest, rel_tol=0.0, abs_tol=1e-9):
        intervals = nearest
    segments = max(1, math.ceil(intervals)) if hi > lo else 0
    if segments + 1 > MAX_GRID:
        raise PricingError("step would exceed %d price grid points; use a larger step" % MAX_GRID)
    grid = [lo + i * step for i in range(segments)] + [hi]
    tc, ch, ex, te = curves(rows, grid)
    not_cheap = [1 - v for v in ch]
    not_exp = [1 - v for v in ex]
    pts = {
        "PMC": cross(grid, tc, not_cheap),
        "PME": cross(grid, not_exp, te),
        "OPP": cross(grid, tc, te),
        "IPP": cross(grid, ch, ex),
    }
    return {"n": len(rows), "points": pts, "range": [pts["PMC"], pts["PME"]],
            "median": {k: sorted(r[i] for r in rows)[len(rows) // 2] for i, k in enumerate(KEYS)}}


def report(res, dropped, price=None, provenance="unknown"):
    if provenance not in PROVENANCES:
        raise PricingError("provenance must be simulated, real-survey, or unknown")
    if price is not None and not _positive(price):
        raise PricingError("current price must be a finite positive number")
    m = lambda v: "n/a" if v is None else "$%.2f" % v
    p = res["points"]
    context = {
        "simulated": "Simulated buyers: use this to pick what to test with actual customers. This does not validate demand.",
        "real-survey": "Real-survey input, as declared by the operator. Stated price preferences do not prove purchases or demand.",
        "unknown": "Source provenance is unverified. Confirm how answers were collected before using the range.",
    }
    L = ["# Price sensitivity", "",
         "%d complete answers%s. Provenance: %s. %s" % (
             res["n"], (", %d dropped (invalid, incomplete or out of order)" % dropped) if dropped else "",
             provenance, context[provenance]), "",
         "| point | price | what it means |", "| --- | ---: | --- |",
         "| PMC | %s | below this, too many think it is too cheap to be good |" % m(p["PMC"]),
         "| OPP | %s | as many say too cheap as too expensive: the least resistance |" % m(p["OPP"]),
         "| IPP | %s | as many call it a bargain as call it expensive |" % m(p["IPP"]),
         "| PME | %s | above this, too many say it is too expensive to buy |" % m(p["PME"]), "",
         "**Acceptable range: %s to %s.**" % (m(p["PMC"]), m(p["PME"])), ""]
    md = res["median"]
    L.append("Median answers: too cheap %s, a bargain %s, getting expensive %s, too expensive %s." % (
        m(md["too_cheap"]), m(md["cheap"]), m(md["expensive"]), m(md["too_expensive"])))
    if price is not None and p["PMC"] is not None and p["PME"] is not None:
        where = "inside" if p["PMC"] <= price <= p["PME"] else ("below" if price < p["PMC"] else "above")
        L += ["", "Your current price, %s, is **%s** the acceptable range." % (m(price), where)]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", help="the panel's answers folder, or a CSV")
    ap.add_argument("--price", type=float, help="your current price, to place it on the range")
    ap.add_argument("--out", help="write the report here (markdown)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--provenance", choices=PROVENANCES, default="unknown",
                    help="how answers were collected; defaults to unverified unknown")
    a = ap.parse_args(argv)
    try:
        if a.price is not None and not _positive(a.price):
            raise PricingError("current price must be a finite positive number")
        rows, dropped = read(a.source)
        res = analyse(rows)
    except (PricingError, FileNotFoundError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    res["provenance"] = a.provenance
    if a.json:
        print(json.dumps(dict(res, dropped=dropped), indent=1))
        return 0
    text = report(res, dropped, a.price, provenance=a.provenance)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s" % a.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
