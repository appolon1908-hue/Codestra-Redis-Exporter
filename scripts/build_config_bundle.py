#!/usr/bin/env python3
"""Build the deterministic Redis Exporter configuration archive."""
from __future__ import annotations
import argparse, gzip, hashlib, json, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "codestra/release/config-bundle.manifest.json"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist/redis-exporter-config.tar.gz")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    paths = []
    for relative, expected in sorted(manifest["files"].items()):
        path = ROOT / relative
        if digest(path) != expected.removeprefix("sha256:"):
            raise SystemExit(f"checksum mismatch for {relative}")
        paths.append(path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path in paths + [MANIFEST]:
                    info = archive.gettarinfo(str(path), arcname=str(path.relative_to(ROOT)))
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ""
                    with path.open("rb") as source:
                        archive.addfile(info, source)
    print(f"CONFIG_BUNDLE_SHA256={digest(args.output)}")

if __name__ == "__main__":
    main()
