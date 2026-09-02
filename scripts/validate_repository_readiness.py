#!/usr/bin/env python3
"""Validate repository-only Redis Exporter release readiness."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = re.compile(r"^[a-z0-9./_-]+@sha256:[0-9a-f]{64}$")
REQUIRED = (
    "README.md", "REPOSITORY_PROFILE.md", "SECURITY.md", ".github/CODEOWNERS",
    "docs/BACKUP_RESTORE_ROLLBACK.md", "docs/UPGRADE.md",
    "codestra/release/runtime-image.lock.json", "codestra/release/config-bundle.manifest.json",
    ".github/workflows/release-config-bundle.yml", "scripts/build_config_bundle.py",
)

def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")

def load(path: str) -> dict:
    value = json.loads((ROOT / path).read_text())
    if not isinstance(value, dict): fail(f"{path} must contain an object")
    return value

def validate() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing: fail(f"missing readiness files: {missing}")
    lock = load("codestra/release/runtime-image.lock.json")
    if not IMAGE.fullmatch(str(lock.get("image", ""))): fail("runtime image is mutable")
    if lock.get("binaryRevisionReadback") != lock.get("upstreamTagCommit"): fail("binary/source revision mismatch")
    if lock.get("productionActivation") is not False: fail("production activation must stay false")
    for relative in ("deploy/compose.yaml", "codestra/runtime-v1/compose.yaml"):
        source = (ROOT / relative).read_text()
        images = re.findall(r"(?m)^\s+image:\s*(\S+)\s*$", source)
        if images != [lock["image"]]: fail(f"{relative} image does not equal runtime lock")
        if re.search(r"(?m)^\s+ports\s*:", source): fail(f"{relative} publishes a host port")
        for token in ("--disable-scrape-endpoint", "--disable-exporting-key-values=true", "--skip-tls-verification=false"):
            if token not in source: fail(f"{relative} missing {token}")
    manifest = load("codestra/release/config-bundle.manifest.json")
    if manifest.get("component") != "redis-exporter" or manifest.get("productionActivation") is not False:
        fail("configuration manifest identity/activation mismatch")
    files = manifest.get("files", {})
    if len(files) != 7: fail("configuration manifest must contain seven governed files")
    for relative, expected in files.items():
        path = ROOT / relative
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(expected)) or "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            fail(f"configuration checksum mismatch: {relative}")
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        for reference in re.findall(r"(?m)^\s*(?:-\s*)?uses:\s*([^\s#]+)", workflow.read_text()):
            if not reference.startswith("./") and not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", reference):
                fail(f"mutable action reference: {workflow.name}: {reference}")
    caller = (ROOT / ".github/workflows/release-config-bundle.yml").read_text()
    authority = "reusable-release-config-bundle.yml@777292781faeca9348d0e2ecdce6ac3f50c91d93"
    if authority not in caller or "component_id: redis-exporter" not in caller:
        fail("release caller authority/component mismatch")

def main() -> None:
    validate()
    print("REDIS_EXPORTER_REPOSITORY_READINESS_SOURCE=PASS")
    print("PRODUCTION_ACTIVATION=NO")

if __name__ == "__main__": main()
