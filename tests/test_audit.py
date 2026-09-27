import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from repo_radar.audit import audit_repository
from repo_radar.cli import main


class AuditTests(unittest.TestCase):
    def test_complete_repository_scores_full_marks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("README.md", "LICENSE", ".gitignore", "pyproject.toml"):
                (root / name).write_text("content", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_example.py").write_text("pass", encoding="utf-8")
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".github" / "workflows" / "ci.yml").write_text("name: CI", encoding="utf-8")

            result = audit_repository(root)

            self.assertEqual(result.percentage, 100)
            self.assertTrue(all(check.passed for check in result.checks))

    def test_missing_files_produce_suggestions(self):
        with tempfile.TemporaryDirectory() as directory:
            result = audit_repository(directory)

            self.assertLess(result.percentage, 50)
            self.assertTrue(any(check.suggestion for check in result.checks))

    def test_large_generated_directories_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "node_modules").mkdir()
            (root / "node_modules" / "bundle.js").write_bytes(b"x" * 2048)

            result = audit_repository(root, max_file_kb=1)
            check = next(item for item in result.checks if item.key == "large_files")

            self.assertTrue(check.passed)

    def test_json_cli_and_threshold_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            output = StringIO()
            with redirect_stdout(output):
                code = main([directory, "--format", "json", "--fail-under", "100"])

            payload = json.loads(output.getvalue())
            self.assertEqual(code, 1)
            self.assertIn("percentage", payload)


if __name__ == "__main__":
    unittest.main()
