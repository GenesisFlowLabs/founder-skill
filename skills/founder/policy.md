# Shared founder policy

Read `~/.claude/CLAUDE.md` when present and the current project's instructions. Work within the user's current authorization, including authorized implementation; do not add generic approval loops.

## Resolve the pack and workspace

Use the absolute read/discovery path of the loaded `SKILL.md` to identify its containing directory. Claude's `CLAUDE_SKILL_DIR` is optional; Codex uses the discovered skill path. Set `SKILL_DIR` to that directory, then resolve folder symlinks before accessing siblings:

```bash
SKILL_DIR="$(cd "$SKILL_DIR" && pwd -P)"
PACK_DIR="$(dirname "$SKILL_DIR")"
```

Read `"$PACK_DIR/founder/policy.md"` and the relevant section of `"$PACK_DIR/founder/profiles.md"`. Invoke scripts with `python3` and absolute paths under `PACK_DIR`. Do not resolve `../founder` against an unresolved installed symlink.

Set `RUN` to the absolute authorized working directory for the decision, outside every git checkout. Paths such as `idea.md` below mean `"$RUN/idea.md"`, never a default subdirectory of the code repository. Reuse current project names, briefs and trackers rather than creating a competing system. Business records follow the existing authorized dossier/tracker routing. Local working copies must be outside git. Finance, health, credentials, personal data and anything from `~/life/` stay on the Mac Studio, outside git, UC-1, VPS and Project-Ops. A combined plan containing finance stays local too. Use an appropriate existing local finance workspace under `~/life/` for financial inputs and outputs. Do not print secrets or put private source material in this public pack.

## Evidence and decisions

Read current source records before reporting names, dates, counts, prices or status. Each material claim has a source path/link and observation date. Separate verified facts, user assumptions, projections and unknowns. Prefer actual interviews, purchase/usage records and paid commitments to simulations. Never invent demand, budgets, testimonials, citations or credentials. Research a changing public claim now through available lightweight read tools; mark unavailable evidence unknown.

Start with the decision, its evidence and the smallest useful workflow. Panels are optional objection exploration, never demand validation, representative samples, upper-bound conversion estimates or financial inputs. Use 12 simulated buyers by default, maximum 20 and at most two concurrent agents. Use fewer or sequential work under resource constraints. Do not start browsers, browser servers, Docker, local models, MCP servers or agent CLIs for this pack. Playwright and Puppeteer are banned on the Mac.

Price a defined outcome or fixed scoping result. Never quote hourly rates. Costs may include internal labor assumptions without turning them into client billing rates. Preserve existing product names. Use US spelling, plain language and no em dashes.

## Execution and output

The current request determines output format, count, destination and read-only boundaries. Named specialist files are suggested layouts, not mandatory side artifacts. Create them only when requested or needed as inputs/outputs of a selected tool or downstream artifact. For one decision memo, combine the relevant analyses there. For read-only source review, preserve the source files and report in the requested format; do not create intermediate artifacts or run writing tools merely because a specialist lists them.

Drafting is distinct from sending, spending, publishing and deploying. Check whether the current authorization covers the specific action, account, audience and environment. Continue covered work; confirm only an uncovered outward or destructive action. Email is always draft-only, with the recipient verified against the contact card. Autonomous external messages require authorized delivery and the AI signature defined in `~/.claude/CLAUDE.md`; a draft never implies sending.

Return: decision/recommendation, evidence and uncertainty, the smallest relevant artifact, and one next action with owner and decision condition. Record business commitments in the existing authorized tracker; keep financial actions local. A prepared plan, local test or draft is not a launch or customer acceptance.
