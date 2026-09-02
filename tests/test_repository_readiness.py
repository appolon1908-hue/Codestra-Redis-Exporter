from __future__ import annotations
import hashlib, json, subprocess, tarfile, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class RepositoryReadinessTests(unittest.TestCase):
    def test_validator(self) -> None:
        subprocess.run(["python3", "scripts/validate_repository_readiness.py"], cwd=ROOT, check=True)
    def test_bundle_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ("one.tar.gz", "two.tar.gz")]
            for path in paths:
                subprocess.run(["python3", "scripts/build_config_bundle.py", "--output", str(path)], cwd=ROOT, check=True)
            self.assertEqual(hashlib.sha256(paths[0].read_bytes()).digest(), hashlib.sha256(paths[1].read_bytes()).digest())
            manifest = json.loads((ROOT / "codestra/release/config-bundle.manifest.json").read_text())
            with tarfile.open(paths[0], "r:gz") as archive: names = set(archive.getnames())
            self.assertEqual(names, set(manifest["files"]) | {"codestra/release/config-bundle.manifest.json"})
    def test_both_manifests_pin_one_private_image(self) -> None:
        lock = json.loads((ROOT / "codestra/release/runtime-image.lock.json").read_text())
        for relative in ("deploy/compose.yaml", "codestra/runtime-v1/compose.yaml"):
            source = (ROOT / relative).read_text()
            self.assertIn(f"image: {lock['image']}", source)
            self.assertNotIn("REDIS_EXPORTER_IMAGE", source)
            self.assertNotIn("\n    ports:\n", source)

if __name__ == "__main__": unittest.main()
