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

## Verified adaptation state, 2026-10-19

Version 1.1.0 is integrated on main. The canonical checkout passed all 80 tests. Independent review findings were fixed and rechecked. The linked installation verified all 24 owned links, twelve skill files and shared policy/profile references, plus all four tool entry points in both assistants. Temporary-home smoke tests also exercised their calculations with synthetic fixtures and verified uninstall.

The installed instructions were applied to a private GFL offer and Panora customer-problem exercise outside this repository. Their recommendations remain proposals, with unresolved commercial terms and real customer evidence clearly separated. No customer contact or application deployment occurred.

No persistent runtime is needed or was launched. Native assistant command menus were not inspected in a new session; start a new session if commands are absent. Installation does not turn the simple financial model into subscription cohort accounting or synthetic panels into real customer evidence.
