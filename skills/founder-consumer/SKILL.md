---
name: founder-consumer
description: Use when explicitly exploring simulated buyer objections or purchasing roles after defining a pitch; real interviews are preferred for demand decisions.
argument-hint: "[--n 12] [--seed S]"
---

# founder-consumer

Resolve this loaded skill directory with `pwd -P`, set `SKILL_DIR` and parent `PACK_DIR`, and read `"$PACK_DIR/founder/policy.md"` plus the relevant `profiles.md` section. Set `RUN` to the authorized workspace, outside git.

Use real interviews, survey responses and purchase evidence first. Run this optional simulation to discover objections, not validate demand or forecast sales. Default 12 buyers, maximum 20; at most two buyer agents concurrently. Do not run a 100-buyer swarm or change permission mode.

1. Write `customer.json` from sourced evidence and explicitly labeled assumptions. For B2B use `"$SKILL_DIR/customer.b2b.example.json"`: `type: "b2b"`, business, target, segments, behaviors under the existing `behaviours` key, and objections. Each segment specifies name, share, roles, organization_budget range, budget_period, organization_size range, authority, workflow_constraints and switching_constraints. Budgets belong to organizations, not personal income. For retail retain `customer.example.json` and its income schema. Do not invent a factual budget or segment share; any simulation allocation is an assumption.
2. Write the exact short offer in `pitch.md`, with known price and terms. If price is unresolved, prefer real discovery first; do not invent one to populate the panel.
3. Choose a dedicated absolute `PANEL_RUN` under `RUN` for this immutable scenario:

```bash
python3 "$SKILL_DIR/panel.py" --dir "$PANEL_RUN" init --customer "$RUN/customer.json" --pitch "$RUN/pitch.md" --n 12
python3 "$SKILL_DIR/panel.py" --dir "$PANEL_RUN" prompts --wave 2
```

An identical run resumes; changed pitch, profile, count or seed requires a new directory. Keep prior runs intact. Dispatch each generated brief to one buyer agent, with no nested agents, at most two at once; sequential execution is fine. If agents are unavailable, report the simulation unrun. Never author answers as the moderator.

```bash
python3 "$SKILL_DIR/panel.py" --dir "$PANEL_RUN" check
python3 "$SKILL_DIR/panel.py" --dir "$PANEL_RUN" tally
```

Retry only missing/broken answers using `prompts`. Save a buyer's own returned JSON with `save ID` on stdin if needed. Record incomplete responses.

Report run path, assumptions, seed, answered count, simulated objections and one real-world next test. Rates describe only this synthetic run, with no representative or upper-bound claim. Never use rates/purchases in financial forecasts, testimonials or acquisition budgets. Keep runs separate; identify a selected run explicitly when producing a plan's `panel/results.md` and `results.json`.
