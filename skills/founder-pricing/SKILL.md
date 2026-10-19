---
name: founder-pricing
description: Use when setting an outcome price, comparing fixed packages or testing price sensitivity against sourced costs and real purchasing evidence.
argument-hint: "[offer or candidate price]"
---

# founder-pricing

Resolve this loaded skill directory with `pwd -P`, set `SKILL_DIR` and parent `PACK_DIR`, and read `"$PACK_DIR/founder/policy.md"` plus the relevant `profiles.md` section. Use authorized `RUN`; keep costs/financial calculations in the local finance workspace.

1. Define the result, included scope, acceptance condition, buyer/budget owner, price unit and term. Preserve unresolved price decisions. Price outcomes or a fixed scoping result, never hours.
2. Prefer actual price conversations, comparable paid work, quotes and procurement evidence. Compare sourced public alternatives with matching setup/support/contract terms. Quote-only pricing stays unknown.
3. Price-sensitivity analysis is optional. Use actual survey CSV columns `too_cheap,cheap,expensive,too_expensive` when available:

```bash
python3 "$SKILL_DIR/van_westendorp.py" "$SURVEY_CSV" --provenance real-survey --out "$RUN/pricing-curve.md"
```

For a selected synthetic run's answers, set `PANEL_RUN` explicitly and label its provenance:

```bash
python3 "$SKILL_DIR/van_westendorp.py" "$PANEL_RUN/answers" --provenance simulated --out "$RUN/pricing-curve.md"
```

Report the source, sample, question wording, units and limitations. A simulated range only suggests questions or candidate tests. It is not willingness-to-pay evidence. A real survey also does not guarantee purchases. Do not require a panel or fabricate a range when responses are absent.

4. Compare justified candidate prices against current explicit costs using:

```bash
python3 "$PACK_DIR/founder-cfo/unit_economics.py" "$FINANCE_RUN/numbers.json" --price "$CANDIDATE_PRICE"
```

`FINANCE_RUN` is the local finance workspace; numeric candidates are labeled assumptions until decided. Missing costs mean no reliable margin claim.

Return the recommendation or unresolved decision, included outcome/terms, evidence, cost floor reference, candidate fixed tiers only if useful, and one real purchase test in the requested format; use `pricing.md` only if a separate artifact is needed. Preserve local-only financial figures. No invented discounts, guarantees or scarcity; model their costs before recommending them. Do not update an agreed price or overwrite baseline financial inputs merely because a sensitivity run looks better.
