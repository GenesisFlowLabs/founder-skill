# GFL founder implementation plan

**Goal:** Install one tested, maintained founder pack from the GFL fork and produce a useful first decision exercise.

**Architecture:** Preserve Markdown skills and four standard-library tools, add a lightweight router and link installer. Work in an isolated branch with disjoint lanes and integrate before installation.

**Tech stack:** Python 3 standard library, Markdown, Git.

**Spec:** `docs/superpowers/specs/2026-10-19-gfl-founder-design.md`.

## Global constraints

- Python standard library only; preserve MIT attribution.
- US spelling and no em dashes.
- No Playwright or Puppeteer on the Mac; no new local models, browser servers, Docker containers, or agent CLIs.
- No private client or financial data in the public repository.
- At most three workers; no worker spawns, installs, commits, pushes, or sends.
- Existing authorization covers implementation and installation. Preserve draft-only email and explicit boundaries for unrelated external actions.

## Review focus

- Missing, nonfinite, boolean, and negative numerical values cannot become misleading valid projections.
- Reinitializing with changed pitch, seed, count, or customer cannot reuse stale answers.
- Business role budgets cannot be presented as a person's income.
- Installer conflicts must be detected before any links change; uninstall cannot remove someone else's work.
- Every installed skill must find shared policy and sibling utilities through the canonical source.

## Task 1: Financial correctness

Owner: finance lane. Files: `skills/founder-cfo/unit_economics.py`, `skills/founder-plan/compile.py`, `tests/test_unit_economics.py`, `tests/test_compile.py`.

- [x] Add regression tests showing incomplete costs and numeric edge cases fail under the original implementation.
- [x] Require explicit validated cost arrays and valid finite model inputs; preserve complete cafe example behavior.
- [x] Return Incomplete on missing/invalid inputs and use projected profitability wording. Report simulated demand separately; never treat its percentage as validation.
- [x] Test CLI/report behavior and focused suite, report exact commands and results.

## Task 2: Panel integrity and B2B roles

Owner: panel lane. Files: `skills/founder-consumer/panel.py`, `skills/founder-consumer/customer.b2b.example.json`, `skills/founder-pricing/van_westendorp.py`, `tests/test_panel.py`, `tests/test_pricing.py`.

- [x] Reproduce stale answers after changed input, add regression tests before fixes.
- [x] Make init resume identical state and refuse changed state without a new directory, leaving existing files intact.
- [x] Add validated B2B role/budget/organization cards with a synthetic example; keep retail compatibility.
- [x] Default to 12 buyers, maximum 20 per run and waves of at most 2. Pricing input must reject nonfinite values and clearly distinguish real survey input from simulations.
- [x] Run focused tests and report stable CLI/input interfaces for prompt integration.

## Task 3: Skill adaptation

Owner: prompt lane. Files: all existing `skills/*/SKILL.md`, new `skills/founder/SKILL.md`, `skills/founder/policy.md`, `skills/founder/profiles.md`. No Python, tests, manifests, or README edits in this lane.

- [x] Read original behavior and record concrete gaps before edits.
- [x] Adapt each specialist to the spec and actual tool interfaces, using current project evidence and small runs.
- [x] Add router and shared policy, one next action per decision. Provide GFL service and Panora Safety/Fleet profile guidance without private customer facts.
- [x] Keep frontmatter concise and scripts portable through resolved skill directory paths.
- [x] Report cases for an independent application test after integration.

## Task 4: Install and maintenance

Owner: integrator. Files: `scripts/install.py`, `tests/test_install.py`, `tests/test_repo.py`, README, plugin manifests, gitignore, release notes and pickup.

- [x] Test missing install destinations, idempotency, conflict preflight, wrong links, dry-run, check, and scoped uninstall with temporary homes.
- [x] Implement symlink installation from the canonical checkout into Claude and Codex skill directories; support the router and all eleven specialists.
- [x] Update fork identity and version, attribution, usage, support matrix, and upstream-update instructions.
- [ ] Run full suite and independent review, address findings, then integrate to the canonical checkout.
- [ ] Install, check every resolved skill/script path, and record native assistant discovery limits without launching heavyweight sessions.

## Task 5: First use and handoff

Owner: integrator, with a reused worker for read-only business evidence after implementation finishes.

- [ ] Use the installed router on one GFL offer decision and one Panora customer-segment decision; preserve unknown facts.
- [ ] Keep sensitive working results outside public git; return useful recommendations in the final handoff.
- [ ] Record test evidence, installation paths, version/commit, resource use, limitations, and next owner decisions. Verify fork destination before publishing reusable code.

## Progress

Initial branch: `gfl/adapt-2026-10-19` from `fd9385b0cfe1b96bebce3898fbd506d73eff5a9d`. Baseline 29 tests passed. Use the stable canonical checkout for installation, and a separate worktree for implementation.

Final preinstallation verification: 80 tests passed; git diff --check passed. Independent review is ready after correction of two functional and two minor findings. Temporary-home installation exercised all four tools through linked paths and removed its own links. Canonical integration and installation are the remaining execution steps.
