# Codestra Redis Exporter

This repository is the service authority for Redis availability, memory, persistence, replication, command, connection, eviction, and keyspace metrics. `appolon1908-hue/Codestra-Prometheus` owns scraping, labels, recording rules, alerts, and retention.

## Least-privilege runtime

The exporter runs as UID/GID 65534 with a read-only filesystem, no Linux capabilities, and no host port. It joins only the private observability and cache networks. Prometheus reaches `redis-exporter:9121/metrics`; the endpoint must not receive a public DNS record, Caddy/Kong route, or host `ports:` mapping.

Redis authentication uses a dedicated monitoring ACL user and an external secret file mounted at `/run/secrets/redis_exporter_password`. Do not place passwords in `REDIS_ADDR`, `.env`, Compose, GitHub Actions, or Prometheus labels. The exporter disables the multi-target `/scrape` endpoint to prevent arbitrary target selection, omits client ports, and skips the Redis `CONFIG` command by default.

The monitoring ACL should permit only commands needed by the reviewed exporter version, normally connection health and read-only server statistics. It must not permit writes, scripting, module administration, replication administration, ACL changes, key reads, key scans, or destructive commands. Validate the exact command set in staging before production.

## Tenant and cardinality safety

Do not configure `check-keys`, key-pattern collection, Lua scripts, client-port export, or database key-name labels. Prometheus adds `environment`, `server`, `application=databases`, `service=redis-exporter`, and `tenant_scope=aggregate`, and strips sensitive/high-cardinality labels centrally.

## Validation

```bash
cp .env.example .env
# Set the reviewed image digest and create the external runtime secret.
docker compose -f deploy/compose.yaml config
docker compose -f deploy/compose.yaml up -d
# From the private observability network:
curl --fail http://redis-exporter:9121/metrics
```

Before target activation, prove `redis_up == 1`, private-only reachability, no `/scrape` endpoint, no inline credential, bounded sample count, required Prometheus labels, and rollback. Deployment and secret creation are separate approved operations.

Promotion is `feature/* -> development -> test -> staging -> production -> main`. Merging does not deploy.
