# GFL Founder pickup

Source: GenesisFlowLabs/founder-skill. Original upstream: Jakeschincariol/founder-skill. Preserve the MIT copyright notice.

This adaptation adds one founder router, eleven adapted specialists, finite explicit financial projections, immutable panel input identity, small B2B simulations, and a conflict-safe linked installer. No running service or browser is required.

Read README and CHANGELOG for behavior and compatibility changes. The implementation design and plan are under docs/superpowers/. Private customer records, financial data, and actual business decision briefs do not belong in this repository.

Verification:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/install.py --check
```

Installed skill folders must resolve to the stable canonical checkout, never a disposable worktree. Start with `/founder` in Claude Code or `$founder` in Codex. Re-read loaded skills after changing them. Fetch upstream manually and review changes before integrating. Default pushes belong to the owned fork, not upstream.
