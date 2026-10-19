# GFL Founder

One entry point for evidence-led business decisions, backed by eleven specialist skills and four small Python tools. Maintained in [GenesisFlowLabs/founder-skill](https://github.com/GenesisFlowLabs/founder-skill).

Start with **`/founder` in Claude Code** or **`$founder` in Codex**. Name the business and the decision. The router reads existing context and picks the smallest useful workflow. It does not run every specialist or generate a buyer swarm by default.

Example: "Use founder to sharpen our fixed-price scoping offer. Use existing evidence and leave the price undecided if cost inputs are missing."

## Install from your maintained checkout

Python 3.8 or newer. No pip packages, API keys, background services, browser engines, or MCP servers are installed. AI reasoning still uses your selected assistant and its normal usage allowance.

```bash
git clone https://github.com/GenesisFlowLabs/founder-skill.git
cd founder-skill
python3 scripts/install.py          # preflight only, no writes
python3 scripts/install.py --apply
python3 scripts/install.py --check
```

The installer creates directory symlinks in `~/.claude/skills/` and `~/.codex/skills/`. All twelve skill folders point at this checkout. Editing the checkout updates the installed content immediately; the assistant must reload a skill to see changed instructions. Start a new assistant session if the installed skills do not appear in the current command list. Installation checks verify files and links; they do not verify an already-open assistant's cached command list.

Use a stable checkout path. Do not install from a temporary review folder or a worktree you plan to remove. The installer preflights every destination and refuses unrelated folders, wrong links, or duplicate founder names in `~/.agents/skills/`. It never overwrites an existing skill. Repeating installation is safe. Ownership is recorded in `~/.config/gfl-founder/install.json`.

```bash
python3 scripts/install.py --uninstall  # removes only this source's owned links
```

Claude plugin manifests are retained under the distinct `gfl-founder` name. Linked installation is recommended for editing this fork. Avoid installing both plugin and linked folders, which would expose duplicate commands.

## Skills

| Skill | Use it for |
| --- | --- |
| `founder` | Select a workflow and return a decision, evidence, unknowns, and next action |
| `founder-board` | Challenge focus, offer value, and differentiation using published frameworks |
| `founder-competitors` | Source-linked alternatives and existing workarounds |
| `founder-consumer` | Optional simulated objection exercises with retail or B2B roles |
| `founder-pricing` | Outcome pricing hypotheses and labeled price-sensitivity input |
| `founder-offer` | Outcome, scope, acceptance, onboarding, and ongoing responsibilities |
| `founder-cfo` | Explicit per-unit costs and twelve-month projections |
| `founder-marketing` | Improve positioning and channels using existing evidence and plans |
| `founder-brand` | Refine an existing identity or investigate a new one when requested |
| `founder-ops` | Delivery, onboarding, support, and ownership routines |
| `founder-launch` | A measurable real-world test and bounded launch plan |
| `founder-plan` | Compile evidence and projections without claiming demand validation |

Every specialist remains directly usable. Shared instructions live in `skills/founder/policy.md`; reusable service, Safety, and Fleet profiles are in `skills/founder/profiles.md`. Company-specific evidence and decisions belong in the authorized workspace, not this public repository.

## Changes from upstream

- Required financial cost arrays. Missing costs produce **Incomplete**; explicit empty arrays represent confirmed zero. Invalid, negative, boolean, and nonfinite model inputs are rejected.
- Success is labeled **Projected profitable**. Simulated buying percentages cannot determine that verdict or validate demand. Projections and customer evidence are reported separately.
- Identical panel runs resume. Changed pitch, customer, seed, or count requires a new directory and preserves prior answers.
- Small panels: 12 buyers by default, maximum 20, maximum two simultaneous buyer agents. Most decisions need no simulation.
- B2B profiles describe organizational roles, budgets, authority, and switching constraints. Retail profiles remain supported.
- Price results carry `simulated`, `real-survey`, or `unknown` provenance. Nonfinite inputs cannot create an unbounded grid loop.
- One maintained source for both assistants, evidence-led wording, and scoped execution boundaries.

## Tools and data

Resolve the checkout path before working in a separate data directory. Set `PRIVATE_RUN` to an authorized data workspace first.

```bash
FOUNDER_CODE="$PWD"
python3 "$FOUNDER_CODE/skills/founder-cfo/unit_economics.py" "$PRIVATE_RUN/numbers.json" --out "$PRIVATE_RUN/cfo.md"
python3 "$FOUNDER_CODE/skills/founder-consumer/panel.py" --dir "$PRIVATE_RUN/panel-v1" init --customer "$PRIVATE_RUN/customer.json" --pitch "$PRIVATE_RUN/pitch.md" --n 12 --seed 7
python3 "$FOUNDER_CODE/skills/founder-consumer/panel.py" --dir "$PRIVATE_RUN/panel-v1" prompts --wave 2
python3 "$FOUNDER_CODE/skills/founder-pricing/van_westendorp.py" "$PRIVATE_RUN/panel-v1/answers" --provenance simulated
python3 "$FOUNDER_CODE/skills/founder-plan/compile.py" --dir "$PRIVATE_RUN" --check
```

`panel.py` creates briefs and tallies answers; it never launches agents or calls an AI service. All four Python tools have no network calls. Research and agent reasoning may use the assistant's configured tools, so local Python alone does not make the entire workflow local inference.

The financial model is a simple repeated-unit projection. For client-month inputs, use `days_per_month: 1` and interpret the legacy per-day fields as client-month counts in each modeled month. There is no subscription cohort, churn, tax, receivables, or retention model. Do not infer LTV or acquisition spend from simulated buyers.

## Updates and verification

Keep `origin` on your fork. Add `upstream` once if it does not already exist:

```bash
git remote add upstream https://github.com/Jakeschincariol/founder-skill.git
git remote set-url --push upstream DISABLED
git config remote.pushDefault origin
git fetch upstream
git diff HEAD..upstream/main -- skills tests
```

Review and integrate selected upstream changes on a branch. Do not blindly reset this fork. Before integrating to the installed checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/install.py --check
```

Installation checks prove link ownership and paths, not whether an open assistant has reread cached instructions. Run a small task through `founder` after updating. Keep private operational and financial outputs outside git; root `founder/`, `runs/`, and `private/` directories are ignored as a backstop.

## Attribution and limits

Forked from [Jake Schincariol's Founder skill](https://github.com/Jakeschincariol/founder-skill), published under MIT. The original copyright and license remain in `LICENSE`. GFL maintains the adaptations here.

The board applies summaries of published frameworks; no endorsement is implied. Simulated responses generate hypotheses and interview questions. They are neither testimonials nor a forecast or statistical upper bound. Real customer evidence, explicit cost inputs, and the user's operating rules govern decisions.
