---
name: founder-cfo
description: Use when projecting unit economics, break-even, delivery capacity or cash needs from explicit costs and volume assumptions.
argument-hint: "[absolute path to numbers.json]"
---

# founder-cfo

Resolve this loaded skill directory with `pwd -P`, set `SKILL_DIR` and parent `PACK_DIR`, and read `"$PACK_DIR/founder/policy.md"` plus the relevant `profiles.md` section. `RUN` must be an authorized local finance workspace on the Mac Studio, outside git.

1. Read current quotes, invoices, capacity records and user decisions. Use `"$SKILL_DIR/example.json"` only as a synthetic schema example. Write `numbers.json` and `cfo-sources.md` with each assumption's source, date and confidence. Never infer zero from missing cost data.
2. Require explicit `variable`, `fixed_monthly` and `startup` arrays of labeled costs; `[]` means confirmed zero. Numerical inputs must be finite JSON numbers, never strings or booleans. Costs/volumes cannot be negative; price and days must be positive. Preserve missing inputs as unknown and report Incomplete instead of filling them.
3. Specify the unit, pretax price, `days_per_month`, `plan_per_day`, optional `capacity_per_day` and twelve `ramp_per_day` assumptions. If no ramp is supplied, disclose that the tool repeats plan volume across all months. For a client-month/seat-month projection, set `days_per_month: 1`; daily-named fields then represent monthly unit counts. Explain that convention in the report. Separate one-time setup and recurring offers rather than mixing unlike units.
4. Include delivery/support effort, infrastructure/API usage, onboarding, payment costs and realistic capacity where relevant. These are internal costs, not an hourly client price. Do not derive volumes, repeat purchases or retention from simulated panels. This tool does not model cohorts, churn, expansion, tax, financing or working-capital timing.

```bash
python3 "$SKILL_DIR/unit_economics.py" "$RUN/numbers.json" --out "$RUN/cfo.md"
python3 "$SKILL_DIR/unit_economics.py" "$RUN/numbers.json" --volume 0.8
```

Use `--price NUMBER` only for a labeled candidate outcome price; it does not authorize changing live prices. Keep invalid tool results visible and correct source inputs before recalculating.

Return projected contribution/margin, break-even/capacity, cash need, strongest sensitivity, missing costs and one next action in the requested format; use `cfo-note.md` only if a separate note is needed. Every reported number comes from the current tool output or a named input. Separate operating profit from startup recovery and actual cash. A positive projection is not proof of profitability or demand. Keep the raw calculated report intact. Route to founder-plan only when consolidation is useful.
