#!/usr/bin/env python3
"""Link the maintained founder checkout into Claude Code and Codex. No network."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile


OWNER = 'GenesisFlowLabs/founder-skill'
NAMES = ('founder', 'founder-board', 'founder-brand', 'founder-cfo',
         'founder-competitors', 'founder-consumer', 'founder-launch',
         'founder-marketing', 'founder-offer', 'founder-ops',
         'founder-plan', 'founder-pricing')
RUNTIMES = ('.claude', '.codex')


class InstallError(Exception):
    pass


def exists(path):
    return path.exists() or path.is_symlink()


def owned_link(destination, source):
    return destination.is_symlink() and destination.resolve() == source


def directory_check(path):
    for parent in (path, *path.parents):
        if exists(parent) and not parent.is_dir():
            raise InstallError('conflict: directory is blocked by %s' % parent)


def state_read(path, source):
    if not exists(path):
        return None
    if path.is_symlink() or not path.is_file():
        raise InstallError('conflict: installer state is not a regular file: %s' % path)
    try:
        state = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise InstallError('conflict: invalid installer state: %s' % exc)
    if (not isinstance(state, dict) or state.get('owner') != OWNER
            or state.get('source') != str(source) or state.get('schema') != 1):
        raise InstallError('conflict: installer state belongs to another source: %s' % path)
    return state


def layout(source, home):
    return [(home / runtime / 'skills' / name, source / 'skills' / name)
            for runtime in RUNTIMES for name in NAMES]


def preflight(source, home, pairs, state_path, require_source):
    if require_source:
        for name in NAMES:
            folder = source / 'skills' / name
            if not (folder / 'SKILL.md').is_file() or folder.resolve() != folder:
                raise InstallError('missing or redirected source skill: %s' % folder)
    for destination, target in pairs:
        directory_check(destination.parent)
        if exists(destination) and not owned_link(destination, target):
            raise InstallError('conflict: refusing to replace %s' % destination)
    alias_root = home / '.agents' / 'skills'
    if (alias_root.resolve() == (home / '.claude' / 'skills').resolve()
            and alias_root.resolve() != (home / '.codex' / 'skills').resolve()):
        raise InstallError('conflict: Claude skills alias the cross-runtime .agents directory; '
                           'reconcile runtime directories before installing duplicate Codex names')
    if alias_root.resolve() != (home / '.codex' / 'skills').resolve():
        for name in NAMES:
            if exists(alias_root / name):
                raise InstallError('conflict: duplicate cross-runtime skill at %s' % (alias_root / name))
    directory_check(state_path.parent)
    return state_read(state_path, source)


def save_state(path, source, pairs):
    record = {'schema': 1, 'owner': OWNER, 'source': str(source),
              'updated_at': datetime.now(timezone.utc).isoformat(),
              'links': [str(p) for p, _ in pairs]}
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix='.install-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            json.dump(record, fh, indent=2)
            fh.write('\n')
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def run(source, home, action):
    source, home = source.expanduser().resolve(), home.expanduser().resolve()
    pairs = layout(source, home)
    state_path = home / '.config' / 'gfl-founder' / 'install.json'
    state = preflight(source, home, pairs, state_path, action != 'uninstall')
    present = [p for p, target in pairs if owned_link(p, target)]
    missing = [p for p, target in pairs if not owned_link(p, target)]
    if action == 'check':
        if missing or state is None:
            raise InstallError('installation incomplete: %d missing links%s' %
                               (len(missing), '; no ownership record' if state is None else ''))
        print('Verified %d links for %d skills in Claude Code and Codex.' % (len(pairs), len(NAMES)))
        print('Source: %s' % source)
        return
    if action == 'uninstall':
        if state is None:
            raise InstallError('no ownership record; refusing to remove links')
        for destination, target in pairs:
            if owned_link(destination, target):
                destination.unlink()
        state_path.unlink()
        print('Removed %d owned links. Source checkout and other skills preserved.' % len(present))
        return
    if action == 'dry-run':
        print('Dry run: %d links to create, %d already correct.' % (len(missing), len(present)))
        print('Source: %s' % source)
        print('Targets: %s' % ', '.join(str(home / r / 'skills') for r in RUNTIMES))
        print('Run with --apply to install; --check to verify; --uninstall to remove owned links.')
        return
    created = []
    try:
        for destination, target in pairs:
            if owned_link(destination, target):
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.symlink_to(target, target_is_directory=True)
            created.append((destination, target))
        save_state(state_path, source, pairs)
    except OSError:
        for destination, target in reversed(created):
            if owned_link(destination, target):
                destination.unlink()
        raise
    print('Installed %d skills through %d links (%d new).' % (len(NAMES), len(pairs), len(created)))
    print('Source: %s' % source)
    print('Skills read directly from this checkout. Start with /founder in Claude Code or $founder in Codex.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1],
                        help='canonical checkout, default: the checkout containing this script')
    parser.add_argument('--home', type=Path, default=Path.home(), help='runtime home, primarily for testing')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--apply', action='store_true', help='create links after full preflight')
    actions.add_argument('--check', action='store_true', help='verify links and ownership record')
    actions.add_argument('--uninstall', action='store_true', help='remove only owned links')
    args = parser.parse_args(argv)
    action = 'apply' if args.apply else 'check' if args.check else 'uninstall' if args.uninstall else 'dry-run'
    try:
        run(args.source, args.home, action)
    except (InstallError, OSError, RuntimeError) as exc:
        print('error: %s' % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
