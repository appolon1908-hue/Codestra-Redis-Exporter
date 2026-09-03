#!/usr/bin/env python3
"""Validate the one-target Redis Exporter password map and runtime invariants."""

from __future__ import annotations

import argparse
import json
import pathlib
import stat
import sys
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME_COMPOSE = ROOT / "codestra" / "runtime-v1" / "compose.yaml"
AUTHORITY_COMPOSE = ROOT / "deploy" / "compose.yaml"
PASSWORD_PATH = "/run/secrets/redis_password_map.json"
PRODUCTION_UID = 59000
PRODUCTION_GID = 59000


def fail(message: str) -> None:
    print(f"REDIS_EXPORTER_PASSWORD_MAP_ERROR={message}", file=sys.stderr)
    raise SystemExit(1)


def normalized_target(redis_addr: str, redis_user: str) -> str:
    addr = redis_addr.strip()
    user = redis_user.strip()
    if not addr:
        fail("REDIS_ADDR is required")
    if not user:
        fail("Redis monitoring ACL user is required")
    try:
        parsed = urlsplit(addr)
    except ValueError as exc:
        fail(f"REDIS_ADDR is invalid: {exc}")
    if parsed.scheme not in {"redis", "rediss"}:
        fail("REDIS_ADDR scheme must be redis or rediss")
    if not parsed.hostname:
        fail("REDIS_ADDR must include a host")
    if parsed.username is not None or parsed.password is not None:
        fail("REDIS_ADDR must not contain credentials")
    if parsed.query or parsed.fragment:
        fail("REDIS_ADDR must not contain query parameters or a fragment")
    try:
        port = parsed.port
    except ValueError as exc:
        fail(f"REDIS_ADDR port is invalid: {exc}")
    if port is None:
        fail("REDIS_ADDR must include an explicit port so password-map lookup spelling is exact")

    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    host = f"{host}:{port}"
    netloc = f"{quote(user, safe='')}@{host}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


def validate_secret_file(
    path: pathlib.Path, expected_uid: int, expected_gid: int
) -> None:
    if path.is_symlink():
        fail("password map may not be a symlink")
    try:
        metadata = path.stat()
    except OSError as exc:
        fail(f"cannot stat password map {path}: {exc}")
    if not stat.S_ISREG(metadata.st_mode):
        fail("password map must be a regular file")
    mode = stat.S_IMODE(metadata.st_mode)
    if metadata.st_uid != expected_uid or metadata.st_gid != expected_gid:
        fail(
            "password map ownership mismatch; "
            f"expected={expected_uid}:{expected_gid}, actual={metadata.st_uid}:{metadata.st_gid}"
        )
    if mode != 0o400:
        fail(f"password map mode must be 0400, actual={mode:04o}")


def load_map(path: pathlib.Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read password map {path}: {exc}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"password map must be valid JSON: {exc}")
    if not isinstance(value, dict):
        fail("password map must be a JSON object")
    return value


def validate_map(value: dict[str, Any], redis_addr: str, redis_user: str) -> str:
    expected = normalized_target(redis_addr, redis_user)
    if set(value) != {expected}:
        fail(
            "password map must contain exactly the configured exporter lookup target; "
            f"expected={expected!r}, actual={sorted(value)}"
        )
    password = value[expected]
    if not isinstance(password, str) or not password:
        fail("password map value must be a non-empty string")
    if "\n" in password or "\r" in password or "\x00" in password:
        fail("password map value may not contain newline, carriage return, or NUL")
    return expected


def validate_compose(path: pathlib.Path, *, require_file_bind: bool) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read {path.relative_to(ROOT)}: {exc}")
    required = (
        "--disable-scrape-endpoint",
        f"--redis.password-file={PASSWORD_PATH}",
        "--export-client-list=false",
    )
    for fragment in required:
        if fragment not in text:
            fail(f"{path.relative_to(ROOT)} is missing runtime invariant: {fragment}")
    forbidden = (
        "REDIS_PASSWORD=",
        "redis://:",
        "--check-keys",
        "--check-single-keys",
        "--count-keys",
        "--export-client-list=true",
    )
    for fragment in forbidden:
        if fragment in text:
            fail(f"{path.relative_to(ROOT)} contains forbidden runtime option: {fragment}")
    if require_file_bind:
        for fragment in (
            "source: ${REDIS_MONITOR_PASSWORD_MAP_FILE:",
            "target: /run/secrets/redis_password_map.json",
            "read_only: true",
            "create_host_path: false",
        ):
            if fragment not in text:
                fail(f"runtime file bind omits {fragment}")
        if "uid: \"59000\"" in text or "gid: \"59000\"" in text:
            fail("Compose file-secret uid/gid remapping is not supported for bind-backed secrets")


def prove_policy() -> None:
    addr = "rediss://redis.internal:6379"
    user = "codestra_monitor"
    key = normalized_target(addr, user)
    validate_map({key: "non-secret-ci-placeholder"}, addr, user)
    unsafe: tuple[Any, ...] = (
        "raw-password",
        ["raw-password"],
        {},
        {"rediss://redis.internal:6379": "secret"},
        {key: ""},
        {key: "secret", "rediss://other.internal:6379": "other"},
        {key: "line1\nline2"},
    )
    for sample in unsafe:
        if not isinstance(sample, dict):
            continue
        try:
            validate_map(sample, addr, user)
        except SystemExit:
            continue
        fail(f"password-map negative test unexpectedly passed: {sample}")
    for invalid_addr in (
        "redis://:password@redis.internal:6379",
        "http://redis.internal:6379",
        "redis://redis.internal:6379?target=other",
        "redis://redis.internal",
        "rediss://redis.internal",
    ):
        try:
            normalized_target(invalid_addr, user)
        except SystemExit:
            continue
        fail(f"target negative test unexpectedly passed: {invalid_addr}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--password-map", type=pathlib.Path)
    parser.add_argument("--redis-addr", default="rediss://redis.internal:6379")
    parser.add_argument("--redis-user", default="codestra_monitor")
    parser.add_argument("--expected-uid", type=int, default=PRODUCTION_UID)
    parser.add_argument("--expected-gid", type=int, default=PRODUCTION_GID)
    args = parser.parse_args()

    prove_policy()
    validate_compose(RUNTIME_COMPOSE, require_file_bind=True)
    validate_compose(AUTHORITY_COMPOSE, require_file_bind=False)
    if args.password_map is not None:
        validate_secret_file(args.password_map, args.expected_uid, args.expected_gid)
        expected = validate_map(
            load_map(args.password_map), args.redis_addr, args.redis_user
        )
        print(f"CODESTRA_REDIS_PASSWORD_MAP_TARGET={expected}")
    print("CODESTRA_REDIS_EXPORTER_RUNTIME_PASSWORD_MAP_PASS=1")


if __name__ == "__main__":
    main()
