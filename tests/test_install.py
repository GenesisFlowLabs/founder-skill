import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'install.py'
NAMES = ['founder', 'founder-board', 'founder-brand', 'founder-cfo',
         'founder-competitors', 'founder-consumer', 'founder-launch',
         'founder-marketing', 'founder-offer', 'founder-ops',
         'founder-plan', 'founder-pricing']


class Install(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='founder-install-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'home'
        self.home.mkdir()
        self.source = self.base / 'source with spaces'
        for name in NAMES:
            folder = self.source / 'skills' / name
            folder.mkdir(parents=True)
            (folder / 'SKILL.md').write_text('---\nname: %s\ndescription: Use when testing.\n---\n' % name)
        (self.source / 'skills/founder/policy.md').write_text('Shared policy')

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--source', str(self.source),
                               '--home', str(self.home), *args],
                              capture_output=True, text=True, timeout=10,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))

    def destinations(self):
        return [self.home / runtime / 'skills' / name
                for runtime in ['.claude', '.codex'] for name in NAMES]

    def test_dry_run_is_default_and_does_not_write(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('dry run', result.stdout.lower())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_install_links_to_source_and_is_idempotent(self):
        first = self.cli('--apply')
        self.assertEqual(first.returncode, 0, first.stderr)
        for target in self.destinations():
            self.assertTrue(target.is_symlink(), target)
            self.assertEqual(target.resolve(), self.source / 'skills' / target.name)
        second = self.cli('--apply')
        self.assertEqual(second.returncode, 0, second.stderr)
        (self.source / 'skills/founder/SKILL.md').write_text('Updated in the owned source')
        self.assertEqual((self.home / '.codex/skills/founder/SKILL.md').read_text(),
                         'Updated in the owned source')
        specialist = self.home / '.claude/skills/founder-offer'
        self.assertEqual((specialist.resolve().parent / 'founder/policy.md').read_text(), 'Shared policy')
        check = self.cli('--check')
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_preflights_conflicts_before_creating_any_links(self):
        conflict = self.home / '.codex/skills/founder-pricing'
        conflict.mkdir(parents=True)
        (conflict / 'mine.txt').write_text('Unrelated skill')
        result = self.cli('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('conflict', result.stderr.lower())
        self.assertFalse((self.home / '.claude').exists())
        self.assertEqual((conflict / 'mine.txt').read_text(), 'Unrelated skill')

    def test_foreign_or_broken_symlink_is_not_replaced(self):
        target = self.home / '.claude/skills/founder'
        target.parent.mkdir(parents=True)
        target.symlink_to(self.base / 'not-ours')
        result = self.cli('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(os.readlink(target), str(self.base / 'not-ours'))
        self.assertFalse((self.home / '.codex').exists())

    def test_check_missing_or_changed_link_is_failure(self):
        self.assertNotEqual(self.cli('--check').returncode, 0)
        self.assertEqual(self.cli('--apply').returncode, 0)
        target = self.home / '.claude/skills/founder'
        target.unlink()
        self.assertNotEqual(self.cli('--check').returncode, 0)

    def test_missing_source_skill_prevents_all_installation(self):
        (self.source / 'skills/founder-pricing/SKILL.md').unlink()
        result = self.cli('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_uninstall_removes_only_owned_links(self):
        self.assertEqual(self.cli('--apply').returncode, 0)
        other = self.home / '.claude/skills/unrelated'
        other.mkdir()
        (other / 'SKILL.md').write_text('Keep')
        result = self.cli('--uninstall')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((other / 'SKILL.md').exists())
        self.assertFalse(any(p.is_symlink() for p in self.destinations()))
        self.assertTrue((self.source / 'skills/founder/SKILL.md').exists())

    def test_uninstall_refuses_to_remove_foreign_replacement(self):
        self.assertEqual(self.cli('--apply').returncode, 0)
        target = self.home / '.codex/skills/founder'
        target.unlink()
        target.mkdir()
        result = self.cli('--uninstall')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(target.is_dir())
        self.assertTrue((self.home / '.claude/skills/founder').is_symlink())

    def test_blocked_parent_fails_before_partial_install(self):
        (self.home / '.codex').write_text('A file blocks this directory')
        result = self.cli('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / '.claude').exists())

    def test_existing_cross_runtime_skill_prevents_duplicate_install(self):
        duplicate = self.home / '.agents/skills/founder'
        duplicate.mkdir(parents=True)
        result = self.cli('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / '.codex').exists())

    def test_claude_alias_to_agents_is_rejected_before_any_install(self):
        shared = self.home / '.agents/skills'
        shared.mkdir(parents=True)
        claude = self.home / '.claude'
        claude.mkdir()
        (claude / 'skills').symlink_to(shared, target_is_directory=True)
        result = self.cli('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cross-runtime', result.stderr)
        self.assertEqual(list(shared.iterdir()), [])
        self.assertFalse((self.home / '.codex').exists())


if __name__ == '__main__':
    unittest.main()
