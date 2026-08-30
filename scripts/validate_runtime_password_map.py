#!/usr/bin/env python3
"""Validate the one-target Redis Exporter password map and runtime invariants."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME_COMPOSE = ROOT / "codestra" / "runtime-v1" / "compose.yaml"
AUTHORITY_COMPOSE = ROOT / "deploy" / "compose.yaml"
PASSWORD_PATH = "/run/secrets/redis_password_map.json"


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
    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    elif parsed.scheme in {"redis", "rediss"}:
        host = f"{host}:6379"
    netloc = f"{quote(user, safe='')}@{host}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


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
            "password map must contain exactly the normalized configured target; "
            f"expected={expected!r}, actual={sorted(value)}"
        )
    password = value[expected]
    if not isinstance(password, str) or not password:
        fail("password map value must be a non-empty string")
    if "\n" in password or "\r" in password or "\x00" in password:
        fail("password map value may not contain newline, carriage return, or NUL")
    return expected


def validate_compose(path: pathlib.Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read {path.relative_to(ROOT)}: {exc}")
    required = (
        "--disable-scrape-endpoint",
        f"--redis.password-file={PASSWORD_PATH}",
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
        "--export-client-list",
    )
    for fragment in forbidden:
        if fragment in text:
            fail(f"{path.relative_to(ROOT)} contains forbidden runtime option: {fragment}")


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
    args = parser.parse_args()

    prove_policy()
    validate_compose(RUNTIME_COMPOSE)
    validate_compose(AUTHORITY_COMPOSE)
    if args.password_map is not None:
        expected = validate_map(
            load_map(args.password_map), args.redis_addr, args.redis_user
        )
        print(f"CODESTRA_REDIS_PASSWORD_MAP_TARGET={expected}")
    print("CODESTRA_REDIS_EXPORTER_RUNTIME_PASSWORD_MAP_PASS=1")


if __name__ == "__main__":
    main()
