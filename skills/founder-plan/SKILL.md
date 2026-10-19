---
name: founder-plan
description: Use when consolidating founder evidence and explicit financial projections into a decision plan or partner summary.
argument-hint: "[absolute workspace path]"
---

# founder-plan

Resolve this loaded skill directory with `pwd -P`, set `SKILL_DIR` and parent `PACK_DIR`, and read `"$PACK_DIR/founder/policy.md"` plus the relevant `profiles.md` section. A plan containing finance must use an authorized local finance `RUN` on the Mac Studio, outside git.

1. Inventory current artifacts and source dates. Use only necessary sections; a missing board, panel or brand is not a reason to run it. Link to existing records and label proposed versus agreed terms.
2. Run the current compiler against this explicit workspace:

```bash
python3 "$SKILL_DIR/compile.py" --dir "$RUN" --check
```

The computed verdict is `Projected profitable`, `Not yet` or `Incomplete`. It evaluates explicit unit costs, operating projection and capacity where supplied. Missing/invalid financial inputs remain Incomplete. Never override or soften a failing check. The legacy `--min-buy-rate` argument is not a demand or financial gate; do not use it as one. No simulated panel is required.

3. Write `summary.md`: decision, verified facts, financial verdict and key calculated numbers, real buyer evidence, uncertainties and one next action with owner. Clearly separate actual results, assumptions, projections and synthetic findings. Missing demand evidence remains missing even when economics project positive.
4. If including a simulated run, explicitly select its unchanged pitch/profile/settings, identify its path/date/seed and keep its results labeled synthetic under `panel/results.md` and `results.json`. Do not merge different runs. Exclude irrelevant or stale artifacts.
5. Compile:

```bash
python3 "$SKILL_DIR/compile.py" --dir "$RUN"
```

Read the generated `business-plan.md` to verify included sections, units, names, dates and wording. For a client-month projection disclose `days_per_month: 1` and monthly interpretation of daily-named fields. The tool does not model cohorts, churn or retention.

Write an optional `one-pager.md` only for an identified audience and approved disclosure scope. Preserve calculated figures and label unagreed asks. Keep finance private; prepare a redacted business summary when external use is requested, and confirm uncovered sharing separately. Return the computed verdict, strongest evidence limit and the one next decision, never a claim that projections prove profitability or demand.
