#!/usr/bin/env python3
"""The buyer panel for founder-consumer. Standard library only, no network.

It does the bookkeeping for a swarm of simulated buyers: it deals one persona card
per buyer from your target-customer profile (income, age, behavior, objection),
writes one brief per buyer for a sub-agent to answer, checks the answers, and
tallies who buys, who doesn't, and why.

    python3 panel.py init --customer founder/customer.json --pitch founder/pitch.md [--n 12] [--seed 7]
    python3 panel.py prompts [--wave 2]      # one brief per buyer still to run, listed in waves
    python3 panel.py check                   # which answers are missing or broken
    python3 panel.py save P003 < reply.txt   # file a buyer's own JSON that it printed instead of writing
    python3 panel.py tally [--out founder/panel/results.md]
    python3 panel.py status

State lives in founder/panel/ (--dir to change it): panel.json, personas.json,
briefs/<id>.md, answers/<id>.json, results.md, results.json.

The tool never answers for a buyer. Every number in results.md is counted from
the answer files the sub-agents wrote. Simulated buyers are a fast, cheap way to
find objections and weak spots. They are not customers: confirm what matters
with real ones (a pre-sale, a waitlist, a landing page with a price on it).
"""

import argparse
import json
import math
import os
import random
import sys

FIRST_NAMES = [
    "Maya", "Jordan", "Priya", "Marcus", "Sofia", "Ethan", "Aisha", "Liam", "Chloe", "Daniel", "Nadia", "Owen",
    "Grace", "Ravi", "Emma", "Kenji", "Zoe", "Luca", "Hana", "Noah", "Fatima", "Caleb", "Isla", "Mateo", "Leah",
    "Omar", "Ava", "Theo", "Mei", "Jonah", "Sara", "Diego", "Ruby", "Kofi", "Nora", "Felix", "Amara", "Ben", "Lina",
    "Sam", "Aria", "Julian", "Keisha", "Marco", "Ines", "Tariq", "Elena", "Hugo", "Yara", "Callum", "Rosa", "Idris",
    "Freya", "Andre", "Leila", "Mason", "Talia", "Rohan", "Esme", "Victor", "Anya", "Kai", "Beatriz", "Declan",
    "Sana", "Jasper", "Min", "Gabriel", "Olivia", "Arjun", "Clara", "Malik", "Iris", "Wes", "Noor", "Rafael", "Ivy",
    "Dev", "Maeve", "Tomas", "Celine", "Adrian", "Lucia", "Hamza", "Poppy", "Ezra", "Sienna", "Darius", "Quinn",
    "Selin", "Rhys", "Nia", "Oscar", "Tess", "Bilal", "Jade", "Luis", "Harper", "Emil", "Kira", "Pablo", "Alma",
    "Seth", "Zara", "Nico", "Farah", "Levi", "June", "Eli", "Ana", "Yusuf", "Lena", "Cole", "Mira", "Raj", "Elle",
    "Finn", "Dana", "Sol", "Ada",
]
REASONS = ["price", "habit", "need", "trust", "quality", "convenience", "timing", "values", "other"]
ANSWER_FIELDS = {"id", "buys", "reason_code", "reason"}
DEFAULT_N = 12
MAX_N = 20
WAVE = 2


class PanelError(Exception):
    pass


# ── dealing ─────────────────────────────────────────────────────────────────────
def _quota(items, n, key="share"):
    """Split n across items by their shares, exactly (largest remainder)."""
    weights = [it.get(key, 1) for it in items]
    scale = max(weights)
    weights = [w / scale for w in weights]
    total = sum(weights)
    raw = [n * w / total for w in weights]
    counts = [int(r) for r in raw]
    order = sorted(range(len(items)), key=lambda i: raw[i] - counts[i], reverse=True)
    for i in order[: n - sum(counts)]:
        counts[i] += 1
    return counts


def _number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value):
    return isinstance(value, list) and bool(value) and all(_text(v) for v in value)


def _range(value, name, integer=False):
    if (not isinstance(value, list) or len(value) != 2
            or not all(_number(v) and v >= 0 for v in value)
            or value[0] > value[1]
            or (integer and not all(isinstance(v, int) for v in value))):
        raise PanelError("%s needs a finite, nonnegative [low, high]%s" %
                         (name, " of integers" if integer else ""))


def validate_customer(c):
    if not isinstance(c, dict):
        raise PanelError("customer.json must be an object")
    for k in ("business", "target"):
        if not _text(c.get(k)):
            raise PanelError("customer.json needs '%s' as nonempty text" % k)
    kind = c.get("type", "retail")
    if kind not in ("retail", "b2b"):
        raise PanelError("customer type must be retail or b2b")
    for k in ("segments", "behaviours"):
        items = c.get(k)
        if not isinstance(items, list) or not items:
            raise PanelError("customer.json needs '%s'" % k)
        for item in items:
            if not isinstance(item, dict) or not _text(item.get("name")):
                raise PanelError("every %s item needs a name" % k)
            share = item.get("share", 1)
            if not _number(share) or share < 0:
                raise PanelError("%s shares must be finite nonnegative numbers" % k)
        if not any(item.get("share", 1) > 0 for item in items):
            raise PanelError("%s needs at least one positive share" % k)
    if not _strings(c.get("objections")):
        raise PanelError("customer.json needs objections as a nonempty list of text")
    if "habits" in c and c["habits"] != [] and not _strings(c["habits"]):
        raise PanelError("habits must be a list of text")
    if kind == "retail":
        _range(c.get("age", [25, 45]), "age", integer=True)
    for s in c["segments"]:
        if kind == "retail":
            _range(s.get("income"), "income")
            continue
        _range(s.get("organization_budget"), "organization_budget")
        _range(s.get("organization_size"), "organization_size", integer=True)
        if s["organization_size"][0] < 1:
            raise PanelError("organization_size must be at least 1")
        if s.get("budget_period") not in ("monthly", "annual", "project"):
            raise PanelError("budget_period must be monthly, annual, or project")
        for k in ("roles", "workflow_constraints", "switching_constraints"):
            if not _strings(s.get(k)):
                raise PanelError("every b2b segment needs %s as a nonempty list of text" % k)
        if not _text(s.get("authority")):
            raise PanelError("every b2b segment needs authority as text")


def deal(customer, n=DEFAULT_N, seed=7):
    """Deal n persona cards. Same customer + n + seed = the same cards, every time."""
    validate_customer(customer)
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= MAX_N:
        raise PanelError("--n must be an integer from 1 to %d" % MAX_N)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise PanelError("--seed must be an integer")
    rng = random.Random(seed)
    age = customer.get("age", [25, 45])
    segs = []
    for s, k in zip(customer["segments"], _quota(customer["segments"], n)):
        segs += [s] * k
    behs = []
    for b, k in zip(customer["behaviours"], _quota(customer["behaviours"], n)):
        behs += [b] * k
    rng.shuffle(segs)
    rng.shuffle(behs)
    names = FIRST_NAMES[:]
    rng.shuffle(names)
    while len(names) < n:
        names += ["%s %d" % (x, len(names) // len(FIRST_NAMES) + 1) for x in FIRST_NAMES]
    objections = customer["objections"]
    habits = customer.get("habits") or []
    cards = []
    for i in range(n):
        s, b = segs[i], behs[i]
        card = {
            "id": "P%03d" % (i + 1),
            "name": names[i],
            "segment": s["name"],
        }
        if customer.get("type", "retail") == "b2b":
            card.update({
                "role": rng.choice(s["roles"]),
                "organization_budget": round(rng.uniform(*s["organization_budget"]), 2),
                "budget_period": s["budget_period"],
                "organization_size": rng.randint(*s["organization_size"]),
                "authority": s["authority"],
                "workflow_constraints": s["workflow_constraints"][:],
                "switching_constraints": s["switching_constraints"][:],
            })
        else:
            card.update({"age": rng.randint(*age),
                         "income": int(round(rng.uniform(*s["income"]), -3))})
        card.update({
            "behaviour": b["name"],
            "behaviour_how": b.get("how", ""),
            "objection": objections[rng.randrange(len(objections))],
            "habit": habits[rng.randrange(len(habits))] if habits else "",
        })
        cards.append(card)
    return cards


# ── state ───────────────────────────────────────────────────────────────────────
def _path(d, *p):
    return os.path.join(d, *p)


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def init(d, customer_path, pitch_path, n=DEFAULT_N, seed=None):
    try:
        customer = _read_json(customer_path)
    except FileNotFoundError:
        raise PanelError("no such file: %s" % customer_path)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise PanelError("invalid customer JSON: %s" % e)
    try:
        with open(pitch_path, encoding="utf-8") as fh:
            pitch = fh.read().strip()
    except FileNotFoundError:
        raise PanelError("no such file: %s (write the pitch first: what you sell, the price, where)" % pitch_path)
    if not pitch:
        raise PanelError("the pitch is empty")
    validate_customer(customer)
    existing = None
    if os.path.exists(_path(d, "panel.json")):
        try:
            existing, saved_cards = load_state(d)
        except (PanelError, json.JSONDecodeError, UnicodeDecodeError):
            raise PanelError("existing panel is incomplete or invalid; use a new run directory")
        if not isinstance(existing, dict):
            raise PanelError("existing panel is invalid; use a new run directory")
    elif os.path.exists(d) and (not os.path.isdir(d) or os.listdir(d)):
        raise PanelError("existing directory has no complete panel; use a new run directory")
    if seed is None:
        seed = existing.get("seed") if existing else random.SystemRandom().randrange(1, 10 ** 6)
    cards = deal(customer, n, seed)
    state = {"n": n, "seed": seed, "customer": customer, "pitch": pitch}
    if existing is not None:
        if existing != state or saved_cards != cards:
            raise PanelError("panel inputs or cards changed; use a new run directory")
        return saved_cards
    _write_json(_path(d, "panel.json"), state)
    _write_json(_path(d, "personas.json"), cards)
    os.makedirs(_path(d, "briefs"), exist_ok=True)
    os.makedirs(_path(d, "answers"), exist_ok=True)
    return cards


def load_state(d):
    try:
        return _read_json(_path(d, "panel.json")), _read_json(_path(d, "personas.json"))
    except FileNotFoundError:
        raise PanelError("no panel in %s: run init first" % d)


BRIEF = """You are a simulated buyer on a buyer panel. A founder is exploring what people in your situation might ask before buying. Your answer is only useful if it is honest: most people do not buy most things, and a polite yes is worse than a clear no.

=== WHO YOU ARE ===
{identity}
How you buy: {behaviour}. {behaviour_how}
{habit_line}The first thing that comes to mind when you hear an offer like this: "{objection}"
You are one of these people: {target}.
=== END ===

=== WHAT IS BEING OFFERED (you see it for the first time) ===
{pitch}
=== END ===

Decide as {name} would, {decision_context}. Do not be agreeable. Do not invent facts about the business beyond what is written above. This is a simulation for finding questions to test, not evidence of real demand.

Create the file {out} with your file-writing tool (do not just print the answer in your reply) containing ONLY this JSON, no markdown fence, nothing else:
{{
  "id": "{id}",
  "buys": true or false,
  "purchases_first_month": how many times you would buy in the first month (0 if you would not buy),
  "reason_code": one of {reasons},
  "reason": "why, in one or two sentences, in your own voice",
  "objection": "the doubt that weighs most for you, in your own words",
  "would_change_my_mind": "the one thing that would flip your answer, or empty",
  "price_too_cheap": the price at which it would seem too cheap to be any good (a number),
  "price_cheap": the price at which it would feel like a bargain (a number),
  "price_expensive": the price at which it starts to feel expensive but you might still buy (a number),
  "price_too_expensive": the price at which you would not buy it at all (a number)
}}
"""


def write_briefs(d, wave=WAVE):
    if isinstance(wave, bool) or not isinstance(wave, int) or not 1 <= wave <= WAVE:
        raise PanelError("--wave must be an integer from 1 to %d" % WAVE)
    state, cards = load_state(d)
    target = state["customer"]["target"]
    todo = []
    for c in cards:
        out = _path(d, "answers", c["id"] + ".json")
        if _answer_ok(out, c["id"]) is None:
            continue
        if state["customer"].get("type", "retail") == "b2b":
            identity = ("{name}, {role}. {segment}. Organization size: {organization_size} people.\n"
                        "Organizational budget: ${organization_budget:,.2f} ({budget_period}), "
                        "not personal income.\nPurchasing authority: {authority}.\n"
                        "Workflow constraints: {workflow}.\nSwitching constraints: {switching}.").format(
                            workflow="; ".join(c["workflow_constraints"]),
                            switching="; ".join(c["switching_constraints"]), **c)
            decision_context = ("within the organization's budget, approval process, existing workflow "
                                "and switching constraints. Do not assume authority you do not have")
        else:
            identity = "{name}, {age}. {segment}. You earn about ${income:,} a year.".format(**c)
            decision_context = "with %s's money, habits and doubts, in a normal week" % c["name"]
        brief = BRIEF.format(pitch=state["pitch"], target=target, out=os.path.abspath(out),
                             identity=identity, decision_context=decision_context,
                             habit_line=("Your day: %s.\n" % c["habit"]) if c.get("habit") else "",
                             reasons=" / ".join(REASONS), **c)
        bp = _path(d, "briefs", c["id"] + ".md")
        with open(bp, "w", encoding="utf-8") as fh:
            fh.write(brief)
        todo.append((c["id"], os.path.abspath(bp)))
    waves = [todo[i:i + wave] for i in range(0, len(todo), wave)]
    return waves


def _answer_ok(path, pid):
    """None if the answer file is good, else a short problem string."""
    if not os.path.exists(path):
        return "missing"
    try:
        a = _read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return "not valid JSON"
    missing = ANSWER_FIELDS - set(a)
    if missing:
        return "missing " + ", ".join(sorted(missing))
    if a.get("id") != pid:
        return "id is %r, expected %s" % (a.get("id"), pid)
    if not isinstance(a.get("buys"), bool):
        return "'buys' must be true or false"
    if a.get("reason_code") not in REASONS:
        return "reason_code %r is not one of %s" % (a.get("reason_code"), ", ".join(REASONS))
    return None


def save(d, pid, text):
    """File a buyer's OWN answer that it printed instead of writing. Never used to answer for a buyer."""
    _, cards = load_state(d)
    if pid not in {c["id"] for c in cards}:
        raise PanelError("no buyer %s on this panel" % pid)
    start = text.find("{")
    if start < 0:
        raise PanelError("no JSON object in the reply")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as e:
        raise PanelError("the reply's JSON does not parse: %s" % e)
    path = _path(d, "answers", pid + ".json")
    _write_json(path, obj)
    prob = _answer_ok(path, pid)
    if prob:
        os.remove(path)
        raise PanelError("%s's answer is not valid (%s); re-run its brief instead" % (pid, prob))
    return path


def check(d):
    _, cards = load_state(d)
    probs = []
    for c in cards:
        p = _answer_ok(_path(d, "answers", c["id"] + ".json"), c["id"])
        if p:
            probs.append((c["id"], p))
    return probs


# ── tally ───────────────────────────────────────────────────────────────────────
def _rate(rows):
    return (sum(1 for r in rows if r["buys"]) / len(rows)) if rows else 0.0


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def tally(d):
    state, cards = load_state(d)
    by_id = {c["id"]: c for c in cards}
    rows, skipped = [], []
    for c in cards:
        path = _path(d, "answers", c["id"] + ".json")
        p = _answer_ok(path, c["id"])
        if p:
            skipped.append((c["id"], p))
            continue
        a = _read_json(path)
        rows.append(dict(by_id[c["id"]], **{k: v for k, v in a.items() if k != "id"}, id=c["id"]))
    if not rows:
        raise PanelError("no valid answers yet: run the briefs first (panel.py prompts)")

    def group(key):
        out = {}
        for r in rows:
            out.setdefault(r[key], []).append(r)
        return sorted(((k, len(v), _rate(v)) for k, v in out.items()), key=lambda t: -t[2])

    b2b = state["customer"].get("type", "retail") == "b2b"
    if b2b:
        # Keep budget periods separate; a project allowance is not monthly spend.
        for period in {r["budget_period"] for r in rows}:
            budgets = sorted(r["organization_budget"] for r in cards if r["budget_period"] == period)
            cut1, cut2 = budgets[len(budgets) // 3], budgets[2 * len(budgets) // 3]
            for r in rows:
                if r["budget_period"] == period:
                    r["budget_band"] = (("under $%s" % format(cut1, ",.2f"))
                                        if r["organization_budget"] < cut1 else
                                        ("$%s and up" % format(cut2, ",.2f"))
                                        if r["organization_budget"] >= cut2 else
                                        ("$%s to $%s" % (format(cut1, ",.2f"), format(cut2, ",.2f"))))
                    r["budget_band"] += " (%s)" % period
    else:
        incomes = sorted(r["income"] for r in cards)
        cut1, cut2 = incomes[len(incomes) // 3], incomes[2 * len(incomes) // 3]
        for r in rows:
            r["income_band"] = ("under $%s" % "{:,}".format(cut1)) if r["income"] < cut1 else (
                ("$%s and up" % "{:,}".format(cut2)) if r["income"] >= cut2 else "$%s to $%s" % ("{:,}".format(cut1), "{:,}".format(cut2)))

    no = [r for r in rows if not r["buys"]]
    yes = [r for r in rows if r["buys"]]

    def reasons(rs):
        out = {}
        for r in rs:
            out.setdefault(r["reason_code"], []).append(r)
        return sorted(((k, v) for k, v in out.items()), key=lambda kv: -len(kv[1]))

    def mean(vals):
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    res = {
        "business": state["customer"]["business"], "seed": state["seed"], "dealt": len(cards),
        "answered": len(rows), "skipped": skipped, "buys": len(yes), "passes": len(no),
        "buy_rate": len(yes) / len(rows),
        "profile_type": "b2b" if b2b else "retail",
        "by_segment": group("segment"), "by_behaviour": group("behaviour"),
        "by_income": [] if b2b else group("income_band"),
        "by_role": group("role") if b2b else [], "by_budget": group("budget_band") if b2b else [],
        "why_not": [(k, len(v), [r["reason"] for r in v[:2]], [r["id"] for r in v[:2]]) for k, v in reasons(no)],
        "why_yes": [(k, len(v), [r["reason"] for r in v[:2]], [r["id"] for r in v[:2]]) for k, v in reasons(yes)],
        "flip": [r["would_change_my_mind"] for r in no if (r.get("would_change_my_mind") or "").strip()],
        "purchases_first_month_per_buyer": mean([_num(r.get("purchases_first_month")) for r in yes]),
        "price_answers": sum(1 for r in rows if all(_num(r.get(k)) is not None for k in
                                                     ("price_too_cheap", "price_cheap", "price_expensive", "price_too_expensive"))),
    }
    return res


def results_md(res):
    pct = lambda v: "%.0f%%" % (v * 100)
    L = ["# Buyer panel: %s" % res["business"], ""]
    L.append("**%d buy · %d pass** (%s buy) out of %d simulated buyers. Seed %s, so the same cards can be dealt again."
             % (res["buys"], res["passes"], pct(res["buy_rate"]), res["answered"], res["seed"]))
    if res["skipped"]:
        L.append("")
        L.append("%d of %d buyers have no valid answer and are left out: %s." % (
            len(res["skipped"]), res["dealt"], ", ".join("%s (%s)" % s for s in res["skipped"][:10])))
    L.append("")
    L.append("These are simulated buyers, not customers. Use this to find objections and weak spots, then confirm the"
             " big ones with real people before you spend.")
    groups = [("By segment", "by_segment"), ("By buying behavior", "by_behaviour")]
    groups += ([("By purchasing role", "by_role"), ("By organizational budget", "by_budget")]
               if res.get("profile_type") == "b2b" else [("By income", "by_income")])
    for title, key in groups:
        L += ["", "## %s" % title, "", "| group | buyers | buy rate |", "| --- | ---: | ---: |"]
        for k, n, r in res[key]:
            L.append("| %s | %d | %s%s |" % (k, n, pct(r), "  (thin)" if n < 8 else ""))
    L += ["", "## Why they pass", "", "| reason | buyers | in their words |", "| --- | ---: | --- |"]
    for k, n, quotes, ids in res["why_not"]:
        L.append("| %s | %d | %s |" % (k, n, " · ".join('"%s" (%s)' % (q.replace("|", "/"), i) for q, i in zip(quotes, ids))))
    L += ["", "## Why they buy", "", "| reason | buyers | in their words |", "| --- | ---: | --- |"]
    for k, n, quotes, ids in res["why_yes"]:
        L.append("| %s | %d | %s |" % (k, n, " · ".join('"%s" (%s)' % (q.replace("|", "/"), i) for q, i in zip(quotes, ids))))
    if res["flip"]:
        L += ["", "## What would flip a no", ""]
        for f in res["flip"][:12]:
            L.append("- %s" % f)
    if res["purchases_first_month_per_buyer"] is not None:
        L += ["", "Buyers say they would buy **%.1f times** in the first month on average." % res["purchases_first_month_per_buyer"]]
    if res["price_answers"]:
        L += ["", "%d buyers gave all four price answers. Run founder-pricing's van_westendorp.py on the answers folder with --provenance simulated." % res["price_answers"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", default=os.path.join("founder", "panel"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--customer", required=True)
    i.add_argument("--pitch", required=True)
    i.add_argument("--n", type=int, default=DEFAULT_N)
    i.add_argument("--seed", type=int)
    p = sub.add_parser("prompts")
    p.add_argument("--wave", type=int, default=WAVE)
    sub.add_parser("check")
    sv = sub.add_parser("save")
    sv.add_argument("id")
    t = sub.add_parser("tally")
    t.add_argument("--out")
    sub.add_parser("status")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "init":
            cards = init(a.dir, a.customer, a.pitch, a.n, a.seed)
            st, _ = load_state(a.dir)
            print("dealt %d buyers (seed %s) into %s. Next: panel.py prompts" % (len(cards), st["seed"], a.dir))
        elif a.cmd == "prompts":
            waves = write_briefs(a.dir, a.wave)
            n = sum(len(w) for w in waves)
            if not n:
                print("every buyer has a valid answer. Next: panel.py tally")
            else:
                print("%d briefs in %d waves of up to %d. Launch one wave at a time:" % (n, len(waves), a.wave))
                for k, w in enumerate(waves, 1):
                    print("wave %d: %s" % (k, " ".join("%s=%s" % job for job in w)))
        elif a.cmd == "check":
            probs = check(a.dir)
            if not probs:
                print("all answers present and valid")
            for pid, prob in probs:
                print("%s: %s" % (pid, prob))
            return 1 if probs else 0
        elif a.cmd == "save":
            print("saved %s" % save(a.dir, a.id, sys.stdin.read()))
        elif a.cmd == "tally":
            res = tally(a.dir)
            text = results_md(res)
            out = a.out or _path(a.dir, "results.md")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(text)
            _write_json(_path(a.dir, "results.json"), res)
            print("%d buy · %d pass (%.0f%%). Wrote %s" % (res["buys"], res["passes"], res["buy_rate"] * 100, out))
        elif a.cmd == "status":
            st, cards = load_state(a.dir)
            probs = check(a.dir)
            print("%d buyers dealt (seed %s), %d answered, %d to go" % (len(cards), st["seed"], len(cards) - len(probs), len(probs)))
    except PanelError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
