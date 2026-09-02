# Codestra Redis Exporter Production Server and Native API Contract

## Authority

- Repository: `appolon1908-hue/Codestra-Redis-Exporter`
- Role: read-only Redis health, capacity, replication, persistence, and latency metrics authority
- Canonical hostname: `rdex.codestra.media`
- Central production host: `37.27.128.39`
- Core host `65.109.65.169`: approved per-instance exporter extension after central certification
- Status: `SOURCE_CONTRACT_PREPARED_NOT_DEPLOYED`

Redis Exporter owns the exporter runtime, approved instance model, metric allowlist, secret-reference contract, release evidence, and rollback. It does not own Redis administration, keys, values, application data, or business mutation.

## Native API surface

| Method | Path | Purpose | Boundary |
|---|---|---|---|
| `GET` | `/metrics` | approved aggregate Redis metrics | private mTLS Prometheus scrape |

The multi-target `/scrape` endpoint must be disabled or unreachable. Unexpected `404` on `/metrics`, unexpected `5xx`, arbitrary target selection, or key/value exposure blocks production.

## Credential and target policy

- Use one exporter per approved Redis instance or an equally strict source-controlled target allowlist.
- Redis credentials come from external runtime secret files/OpenBao and use the exporter-supported format.
- Do not embed a password in a URI, environment dump, Compose file, repository, metric, label, or log.
- The Redis monitoring identity is read-only and cannot execute mutation or dangerous commands.
- Key names, key values, customer identifiers, queues containing payload data, and command arguments are not exported.
- Native metrics remain private and are scraped only by the approved Prometheus identity.

## Production gates

```text
PROTECTED_PRODUCTION_SHA=PASS
READ_ONLY_REDIS_IDENTITY=PASS
RUNTIME_SECRET_REFERENCE=PASS
PASSWORD_IN_URI=NO
ARBITRARY_SCRAPE_TARGET=NO
TARGET_ALLOWLIST=PASS
KEY_VALUE_EXPORT=NO
MTLS_SCRAPE=PASS
IMMUTABLE_IMAGE_DIGEST=PASS
IMAGE_SIGNATURE=PASS
SBOM=PASS
PROVENANCE=PASS
SECRET_SCAN=PASS
ROLLBACK_MANIFEST=PASS
```

## Runtime certification

```text
GET_/metrics=PASS
GET_/scrape_ARBITRARY_TARGET=DENIED
UNAUTHENTICATED_SCRAPE_DENIED=PASS
MTLS_CLIENT_VERIFY=PASS
READ_ONLY_REDIS_ACCESS=PASS
MEMORY_CLIENTS_LATENCY=PASS
REPLICATION_PERSISTENCE=PASS
EVICTIONS_AND_ERRORS=PASS
KEY_NAMES_EXPOSED=0
KEY_VALUES_EXPOSED=0
CREDENTIALS_EXPOSED=0
UNEXPECTED_404=0
UNEXPECTED_5XX=0
SOURCE_RUNTIME_DRIFT=0
```

## Repository-first remediation

Keep the old healthy exporter until the candidate passes. Fix every target, secret-format, or metric defect here with regression tests; commit/push; obtain exact-head CI/review; merge normally; rebuild/sign; update the BOM; and retry. Never edit a production exporter URI or credential mapping without updating this repository.

## Safety

This document does not deploy Redis Exporter or grant Redis access. SSH changes, business writes, communications delivery, provider effects, lending, payments, and trading remain outside scope and disabled.