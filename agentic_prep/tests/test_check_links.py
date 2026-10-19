"""Anonymous synthetic filesystem regressions; no personal files or network."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/check_links.py'
spec = importlib.util.spec_from_file_location('check_links', SCRIPT)
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


class LinkAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.root = self.repo / 'course'
        self.root.mkdir()

    def write(self, path, text=''):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return p

    def audit(self, text):
        self.write('course/README.md', text)
        return checker.audit(self.root, self.repo)[1:]

    def test_links_images_reference_html_and_encoded_spaces(self):
        self.write('assets/a b.txt')
        errors, _ = self.audit('[a](<../assets/a b.txt>)\n![x](../assets/a%20b.txt?q=1#x)\n[r][id]\n[id]: ../assets/a%20b.txt\n<img src="../assets/a%20b.txt">')
        self.assertEqual([], errors)

    def test_missing_link_and_reference_have_line_numbers(self):
        errors, _ = self.audit('intro\n[x](missing.md)\n[x][unknown]')
        self.assertEqual([2, 3], [e.line for e in errors])

    def test_relative_paths_inside_code_are_checked(self):
        errors, _ = self.audit('`../absent/lab.py`\n```python\npath = "../missing/data.json"\n```')
        self.assertEqual({'inline path', 'code path'}, {e.kind for e in errors})

    def test_shell_cd_and_multiple_commands(self):
        self.write('labs/run.py')
        self.write('course/nope.py')
        errors, _ = self.audit('```bash\ncd labs && python3 run.py\npython3 missing.py\n```')
        self.assertEqual(['missing.py'], [e.target for e in errors])

    def test_fences_reset_cwd_and_tilde_fence(self):
        self.write('labs/run.py')
        self.write('root.py')
        self.assertEqual([], self.audit('~~~sh\ncd labs\npython3 run.py\n~~~\n```bash\npython3 root.py\n```')[0])

    def test_inline_command_uses_repo_root(self):
        self.write('scripts/check.py')
        self.assertEqual([], self.audit('Run `python3 scripts/check.py`')[0])
        self.assertTrue(self.audit('Run `python3 scripts/absent.py`')[0])

    def test_unittest_discover_pattern_is_not_a_root_file(self):
        self.write('tests/test_demo.py')
        self.assertEqual([], self.audit('```bash\npython3 -m unittest discover -s tests -p test_demo.py -v\n```')[0])
        self.assertTrue(self.audit('```bash\npython3 -m unittest discover -s absent -v\n```')[0])

    def test_discovery_cannot_silently_run_zero_tests(self):
        self.write('tests/other.py')
        errors, _ = self.audit('```bash\npython3 -m unittest discover -s tests -p test_missing.py\n```')
        self.assertIn('test pattern', [e.kind for e in errors])

    def test_escape_and_symlink_are_rejected(self):
        outside = self.repo.parent / 'outside.txt'
        (self.root / 'link').symlink_to(outside)
        errors, _ = self.audit('[escape](../../outside.txt)\n[symlink](link)')
        self.assertEqual(['outside repository'] * 2, [e.detail for e in errors])

    def test_urls_fragments_and_api_routes_are_not_files(self):
        self.assertEqual([], self.audit('[web](https://example.test/x) [mail](mailto:a@example.test) [anchor](#x)\n`POST /jobs/{id}`')[0])

    def test_machine_specific_path_is_an_error(self):
        errors, _ = self.audit('```bash\ncd /Users/example/private\n```')
        self.assertIn('machine path', [e.kind for e in errors])

    def test_dynamic_paths_warn_instead_of_claiming_validation(self):
        errors, warnings = self.audit('```bash\npython3 "$LAB/run.py"\n```')
        self.assertEqual([], errors)
        self.assertEqual('dynamic path', warnings[0].detail)

    def test_example_annotation_is_explicit_and_reported(self):
        errors, warnings = self.audit('`./sample.py` <!-- path-check: example user creates this file -->')
        self.assertEqual([], errors)
        self.assertEqual('documented example', warnings[0].kind)

    def test_cli_failure_and_success_from_another_cwd(self):
        self.write('course/README.md', '[x](missing.md)')
        args = [sys.executable, str(SCRIPT), '--root', str(self.root), '--repo-root', str(self.repo)]
        result = subprocess.run(args, cwd=self.tmp.name, capture_output=True, text=True)
        self.assertEqual(1, result.returncode)
        self.assertIn('README.md:1:', result.stdout)
        self.write('course/missing.md')
        self.assertEqual(0, subprocess.run(args, capture_output=True).returncode)


if __name__ == '__main__':
    unittest.main()
