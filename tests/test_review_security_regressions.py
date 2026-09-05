"""Regression coverage for direct Git transports and literal Redis credentials."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("review_security_validator", ROOT / "scripts/validate_repository_security.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
SCANNER = ROOT / "scripts/reject_repository_secrets.sh"
APPROVED = 'git push origin "HEAD:refs/heads/${SYNC_BRANCH}"'


class ReviewSecurityRegressions(unittest.TestCase):
    def scan(self, source: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "fixture.txt").write_text(source)
            return subprocess.run(["bash", str(SCANNER), directory], capture_output=True, text=True, timeout=30, check=False)

    def test_direct_git_transport_executables_are_rejected(self) -> None:
        for executable in ("git-push", "/usr/lib/git-core/git-push", "/usr/lib/git-core/git-send-pack", "/usr/lib/git-core/git-http-push"):
            for command in (f"{executable} origin HEAD:refs/heads/main", f"bash -c '{executable} origin HEAD:refs/heads/main'"):
                with self.subTest(command=command):
                    with self.assertRaisesRegex(ValueError, "protected_branch_sync_forbidden"):
                        VALIDATOR.reject_protected_pushes(APPROVED + "\n" + command)

    def test_existing_alias_rejection_remains_effective(self) -> None:
        for command in ("git -c alias.ship=push ship origin HEAD:refs/heads/main", "git -calias.ship=push ship origin HEAD:refs/heads/main", "git --config-env=alias.ship=SHIP ship origin HEAD:refs/heads/main"):
            with self.subTest(command=command):
                with self.assertRaisesRegex(ValueError, "protected_branch_sync_forbidden"):
                    VALIDATOR.reject_protected_pushes(APPROVED + "\n" + command)

    def test_exact_reviewed_push_is_still_allowed(self) -> None:
        VALIDATOR.reject_protected_pushes(APPROVED)

    def test_short_and_metacharacter_passwords_are_rejected(self) -> None:
        for key in ("REDIS_PASSWORD", "REDIS_EXPORTER_BASIC_AUTH_PASSWORD"):
            for value in ("x", "abc", "'$ecret123'", '"$ecret123"', "' '" , "'{literal}'", "'!'"):
                for separator in ("=", ": "):
                    with self.subTest(key=key, value=value, separator=separator):
                        result = self.scan(key + separator + value + "\n")
                        self.assertEqual(result.returncode, 1, result.stderr)
                        self.assertIn("secret pattern detected", result.stderr)
                        self.assertNotIn(value, result.stderr)

    def test_json_passwords_are_rejected(self) -> None:
        result = self.scan('{"' + "REDIS_PASSWORD" + '": "$ecret123"}\n')
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_only_complete_nonliteral_environment_references_are_allowed(self) -> None:
        key = "REDIS_" + "PASSWORD"
        for value in ("${REDIS_PASSWORD_FROM_SECRET_FILE}", '"${REDIS_PASSWORD_FROM_SECRET_FILE}"'):
            result = self.scan(key + "=" + value + "\n")
            self.assertEqual(result.returncode, 0, result.stderr)
        for value in ("'${REDIS_PASSWORD_FROM_SECRET_FILE}'", "${PASSWORD:-literal}", "${PASSWORD}suffix", '"${PASSWORD}"suffix', "$ecret"):
            result = self.scan(key + "=" + value + "\n")
            self.assertEqual(result.returncode, 1, result.stderr)

    def test_scanner_errors_remain_distinct_from_clean_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "dangling").symlink_to(Path(directory) / "missing")
            result = subprocess.run(["bash", str(SCANNER), directory], capture_output=True, text=True, timeout=30, check=False)
            self.assertGreater(result.returncode, 1)
            self.assertIn("symbolic link", result.stderr)


if __name__ == "__main__":
    unittest.main()
