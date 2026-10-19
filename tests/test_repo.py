import json
import os
import re
import unittest

from _load import ROOT, SKILLS_DIR

SKILLS = ["founder", "founder-board", "founder-marketing", "founder-cfo", "founder-consumer", "founder-launch",
          "founder-pricing", "founder-offer", "founder-competitors", "founder-brand", "founder-ops", "founder-plan"]
OWNED_REPO = "https://github.com/GenesisFlowLabs/founder-skill"


def frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1) if m else ""), text


EM = chr(0x2014)  # built in code so this file does not trip its own check


def text_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for f in files:
            if f.endswith((".md", ".py", ".json", ".txt")) or f in ("LICENSE", ".gitignore"):
                yield os.path.join(base, f)


class Repo(unittest.TestCase):
    def test_router_and_eleven_specialist_folders(self):
        found = sorted(d for d in os.listdir(SKILLS_DIR) if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md")))
        self.assertEqual(found, sorted(SKILLS))

    def test_frontmatter_name_and_description(self):
        for s in SKILLS:
            fm, text = frontmatter(os.path.join(SKILLS_DIR, s, "SKILL.md"))
            self.assertIn("name: %s\n" % s, fm + "\n", s)
            self.assertRegex(fm, r"description: ", s)
            self.assertLessEqual(len(fm), 1024, s)
            self.assertIn("Use when", fm, s)
            self.assertTrue(text[len(fm):].strip(), s)

    def test_tools_named_in_skills_exist(self):
        tools = set()
        for s in SKILLS:
            _, text = frontmatter(os.path.join(SKILLS_DIR, s, "SKILL.md"))
            for variable, relative in re.findall(r"\$(?:\{)?(SKILL_DIR|PACK_DIR)(?:\})?/([\w.\-/]+\.(?:py|md|json))", text):
                base = os.path.join(SKILLS_DIR, s) if variable == "SKILL_DIR" else SKILLS_DIR
                self.assertTrue(os.path.isfile(os.path.normpath(os.path.join(base, relative))),
                                "%s: %s/%s" % (s, variable, relative))
                if relative.endswith('.py'):
                    tools.add(os.path.basename(relative))
        self.assertEqual(tools, {'panel.py', 'unit_economics.py', 'van_westendorp.py', 'compile.py'})

    def test_plugin_manifests(self):
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json")) as fh:
            plugin = json.load(fh)
        self.assertEqual(plugin["name"], "gfl-founder")
        self.assertEqual(plugin["repository"], OWNED_REPO)
        self.assertEqual(plugin["homepage"], OWNED_REPO)
        self.assertEqual(plugin["license"], "MIT")
        with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")) as fh:
            market = json.load(fh)
        self.assertEqual(market["name"], "gfl-founder")
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])
        self.assertEqual(market["plugins"][0]["source"], "./")
        self.assertEqual(market["plugins"][0]["homepage"], OWNED_REPO)

    def test_fork_keeps_attribution_and_documents_owned_install(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
            readme = " ".join(fh.read().split())
        self.assertIn(OWNED_REPO, readme)
        self.assertIn("Jakeschincariol/founder-skill", readme)
        self.assertIn("python3 scripts/install.py --apply", readme)
        with open(os.path.join(ROOT, "LICENSE"), encoding="utf-8") as fh:
            license_text = fh.read()
        self.assertIn("Copyright (c) 2026 Jake Schincariol", license_text)
        self.assertIn("MIT License", license_text)

    def test_examples_parse(self):
        for rel in ("founder-cfo/example.json", "founder-consumer/customer.example.json",
                    "founder-consumer/customer.b2b.example.json"):
            with open(os.path.join(SKILLS_DIR, rel), encoding="utf-8") as fh:
                json.load(fh)

    def test_markdown_local_file_links_resolve(self):
        for s in SKILLS:
            path = os.path.join(SKILLS_DIR, s, "SKILL.md")
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if not target.startswith(("http:", "https:", "#")):
                    self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(path), target)),
                                    "%s: broken reference %s" % (s, target))

    def test_no_em_dashes(self):
        for path in text_files():
            with open(path, encoding="utf-8") as fh:
                self.assertNotIn(EM, fh.read(), os.path.relpath(path, ROOT))


if __name__ == "__main__":
    unittest.main()
