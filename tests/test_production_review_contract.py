from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class ProductionReviewContractTests(unittest.TestCase):
    def test_runtime_requires_explicit_port_and_ownership_preserving_bind(self) -> None:
        compose_path = ROOT / "codestra/runtime-v1/compose.yaml"
        text = compose_path.read_text(encoding="utf-8")
        compose = yaml.safe_load(text)
        service = compose["services"]["redis-exporter"]

        self.assertEqual(service["user"], "59000:59000")
        self.assertNotIn("secrets", service)
        self.assertIn("explicit port", text)
        mounts = [mount for mount in service["volumes"] if isinstance(mount, dict)]
        self.assertEqual(len(mounts), 1)
        self.assertEqual(mounts[0]["target"], "/run/secrets/redis_password_map.json")
        self.assertIs(mounts[0]["read_only"], True)
        self.assertIs(mounts[0]["bind"]["create_host_path"], False)
        self.assertIn("REDIS_MONITOR_PASSWORD_MAP_FILE", mounts[0]["source"])

        validator = (ROOT / "scripts/validate_runtime_password_map.py").read_text()
        self.assertIn("must include an explicit port", validator)
        self.assertIn("password map ownership mismatch", validator)
        self.assertIn("password map mode must be 0400", validator)

    def test_upstream_authority_is_exact_deterministic_and_reviewed(self) -> None:
        authority = json.loads((ROOT / "CODESTRA_UPSTREAM.json").read_text())
        lock = json.loads((ROOT / "CODESTRA_UPSTREAM_LOCK.json").read_text())
        runtime = json.loads(
            (ROOT / "codestra/release/runtime-image.lock.json").read_text()
        )
        workflow = (ROOT / ".github/workflows/upstream-source-sync.yml").read_text()

        expected = runtime["upstreamTagCommit"]
        self.assertRegex(expected, r"^[0-9a-f]{40}$")
        self.assertEqual(authority["upstream_ref"], expected)
        self.assertEqual(lock["upstream_ref"], expected)
        self.assertEqual(lock["upstream_commit"], expected)
        self.assertIs(lock["deterministic"], True)
        self.assertNotIn("synchronized_at", lock)
        self.assertIn("branches: [development]", workflow)
        self.assertIn("gh pr create", workflow)
        self.assertNotIn("git push origin HEAD:main", workflow)
        self.assertIn("config-bundle.manifest.json", workflow)

    def test_configuration_manifest_hashes_every_governed_file(self) -> None:
        manifest = json.loads(
            (ROOT / "codestra/release/config-bundle.manifest.json").read_text()
        )
        self.assertIs(manifest["productionActivation"], False)
        for relative, expected in manifest["files"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertFalse(path.is_symlink(), relative)
            actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)


if __name__ == "__main__":
    unittest.main()
