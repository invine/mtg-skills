"""Exercise the installed hook through Git's public pre-push interface."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class GuardTests(unittest.TestCase):
    def test_outgoing_revision_is_checked_and_original_hook_receives_input(self):
        guard = Path(__file__).with_name("validation_guard.py")
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            def git(*args):
                return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
            git("init", "-q")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.invalid")
            original = repo / "original-hooks"
            original.mkdir()
            marker = repo / "original-input"
            hook = original / "pre-push"
            hook.write_text(f"#!{sys.executable}\nimport sys\nfrom pathlib import Path\nPath({str(marker)!r}).write_text(sys.stdin.read())\n")
            hook.chmod(0o755)
            (original / "helper.sh").write_text("true\n")
            precommit = original / "pre-commit"
            precommit.write_text('#!/bin/sh\n. "$(dirname "$0")/helper.sh"\n')
            precommit.chmod(0o755)
            git("config", "core.hooksPath", str(original))
            skill = repo / "review"
            (skill / "scripts").mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: review-mtg-limited-games\ndescription: Test\n---\n")
            test = skill / "scripts/test_example.py"
            test.write_text("import unittest\nclass Example(unittest.TestCase):\n def test_example(self): self.assertTrue(True)\n")
            git("add", "review")
            git("commit", "-qm", "passing")
            passed = git("rev-parse", "HEAD")
            subprocess.run([sys.executable, "-B", str(guard), "install", str(repo)], check=True, capture_output=True)
            installed = Path(git("config", "core.hooksPath")) / "pre-push"
            payload = f"refs/heads/main {passed} refs/heads/main {'0' * 40}\n"
            test.write_text("BROKEN WORKTREE IS NOT THE OUTGOING COMMIT\n")
            result = subprocess.run([str(installed), "origin", "https://example.invalid"], input=payload,
                                    text=True, capture_output=True, cwd=repo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(marker.read_text(), payload)
            git("add", "review")
            git("commit", "-qm", "failing")
            failed = git("rev-parse", "HEAD")
            test.write_text("# clean working tree cannot hide a broken outgoing revision\n")
            bad_payload = payload.replace(passed, failed)
            result = subprocess.run([str(installed), "origin", "https://example.invalid"], input=bad_payload,
                                    text=True, capture_output=True, cwd=repo)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(), payload)


if __name__ == "__main__":
    unittest.main()
