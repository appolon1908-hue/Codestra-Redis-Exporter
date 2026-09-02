# Repository profile — Codestra Redis Exporter

- Repository: `appolon1908-hue/Codestra-Redis-Exporter`
- Component ID: `redis-exporter`
- Purpose: bounded, aggregate Redis infrastructure metrics through a least-privilege ACL identity
- Non-goals: arbitrary target probing, key/value export, Redis mutation, business data access or public exposure
- Branch path: `feature/* -> development -> test -> staging -> production -> main`
- Canonical manifest: `deploy/compose.yaml`; `codestra/runtime-v1/compose.yaml` is compatibility-only
- Upstream: `oliver006/redis_exporter` v1.90.0, commit `072bd8bdabb60de075206fbebc9698edb1fff8f1`
- Runtime: `docker.io/oliver006/redis_exporter@sha256:a129504e65b87c54f79bc92f1afc403475e8ff646a3d7512de469904ceddf986`
- Artifact model: verified upstream image plus signed Codestra configuration bundle
- Health/readiness: private `/metrics`; `redis_up == 1` against the one approved target
- Secrets: one OpenBao-rendered password-map file; no scalar password or credential URI
- Exposure: private observability/cache networks, no host port or edge route
- Persistence: none; Redis owns data
- Release/rollback: exact image/config digests and checksum; previous artifacts must be pullable

Current verdict: `SOURCE_PREPARED_NOT_DEPLOYED`. Registry release and rollback identities are not claimed by this profile.
