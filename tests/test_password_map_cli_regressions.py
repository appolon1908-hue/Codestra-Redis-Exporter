"""Exercise the actual CLI without connecting to Redis or starting containers."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_runtime_password_map.py"


class PasswordMapCliRegressions(unittest.TestCase):
    def invoke(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True, text=True, check=False, timeout=30,
        )

    def test_missing_port_is_rejected_without_password_file(self) -> None:
        for address in ("redis://redis.internal", "rediss://redis.internal"):
            with self.subTest(address=address):
                result = self.invoke("--redis-addr", address)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("must include an explicit port", result.stderr)
                self.assertNotIn("PASSWORD_MAP_PASS=1", result.stdout)

    def test_other_invalid_cli_targets_are_not_ignored(self) -> None:
        for address in ("http://redis.internal:6379", "redis://redis.internal:6379?target=other"):
            with self.subTest(address=address):
                result = self.invoke("--redis-addr", address)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("PASSWORD_MAP_PASS=1", result.stdout)

    def test_empty_cli_user_is_rejected_without_password_file(self) -> None:
        result = self.invoke("--redis-user", "")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("monitoring ACL user is required", result.stderr)

    def test_valid_default_static_validation_still_passes(self) -> None:
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASSWORD_MAP_PASS=1", result.stdout)

    def test_real_file_ownership_and_single_target_checks_remain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.json"
            path.write_text(json.dumps({"rediss://codestra_monitor@redis.internal:6379": "synthetic-ci-only"}))
            path.chmod(0o400)
            arguments = ("--password-map", str(path), "--expected-uid", str(os.getuid()), "--expected-gid", str(os.getgid()))
            result = self.invoke(*arguments)
            self.assertEqual(result.returncode, 0, result.stderr)
            path.chmod(0o600)
            result = self.invoke(*arguments)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("mode must be 0400", result.stderr)


if __name__ == "__main__":
    unittest.main()
