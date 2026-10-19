# Changelog

## 1.1.0 - GFL maintained pack

- Added a founder router and shared service/B2B guidance across eleven specialists.
- Added linked Claude Code and Codex installation from one maintained checkout, with preflight conflict checks and scoped uninstall.
- Required explicit financial costs and finite numerical inputs. Plans distinguish projections from actual profitability and demand.
- Separated simulated buyer output from financial verdicts, marketing forecasts, and acquisition budgets.
- Preserved panel runs when inputs change; added B2B organizational purchasing roles and small bounded runs.
- Rejected nonfinite pricing data before calculation and capped grid size. Price input provenance is explicit.
- Preserved upstream MIT attribution and moved fork metadata to GenesisFlowLabs.

### Compatibility changes

- A positive financial verdict is now `Projected profitable`; `--min-buy-rate` is a deprecated no-op.
- Missing cost arrays must be supplied explicitly. JSON numbers must be actual numeric values, not strings or booleans.
- Panels now default to 12 buyers, maximum 20, with waves of at most two. Older large runs must be archived; create a separate small run instead of rewriting their state.
- A changed panel pitch/profile/count/seed requires a new run directory.
- Install from a stable source checkout. Existing unrelated or duplicate skill installations must be reconciled before linking.

### Model limitations

The financial tool remains a simple repeated-unit projection with a twelve-month horizon. Monthly client units use `days_per_month: 1` and a documented interpretation of legacy daily field names. Churn, retention, tax, payment timing, and acquisition cohorts require separate validated models. Simulations cannot establish demand, expected conversion, or an upper bound on real conversion.

## 1.0.0 - Upstream

Original eleven-skill pack by Jake Schincariol. See the retained MIT license and upstream repository linked in README.
