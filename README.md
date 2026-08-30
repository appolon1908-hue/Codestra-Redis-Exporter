# Codestra Redis Exporter

This repository is the service authority for Redis availability, memory, persistence, replication, command, connection, eviction, latency, error, and keyspace infrastructure metrics. `appolon1908-hue/Codestra-Prometheus` owns scraping, canonical labels, recording rules, alerts, SLO evaluation, and retention.

## Least-privilege runtime

The exporter runs as UID/GID 65534 with a read-only filesystem, no Linux capabilities, `no-new-privileges`, and no host port. It joins only the private observability and cache networks. Prometheus reaches `redis-exporter:9121/metrics`; `rdex.codestra.media` is an ownership/DNS identifier and does not authorize a public endpoint, Caddy/Kong route, or Docker `ports:` mapping.

Redis authentication uses a dedicated monitoring ACL user and an external secret mounted at `/run/secrets/redis_exporter_password`. Passwords must not appear in `REDIS_ADDR`, `.env`, Compose, GitHub Actions, logs, or Prometheus labels. The exporter disables the multi-target `/scrape` endpoint, omits client ports, and skips the Redis `CONFIG` command by default.

The monitoring ACL must permit only the commands required by the reviewed exporter version for connection health and read-only server statistics. It must not permit writes, scripting, module administration, replication administration, ACL changes, key reads, key scans, or destructive commands.

## Corporate metric and privacy contract

The corporate profile covers memory pressure, clients, commands, keyspace aggregate counts, evictions, replication, persistence, latency, blocked clients, and exporter errors across approved Redis instances. It uses controlled business/application/environment/deployment attribution while forbidding key names, values, scripts, customer data, session contents, raw payloads, and high-cardinality client-port labels.

See `codestra/enterprise-profile.v1.json` and `codestra/docs/CORPORATE-FEATURES.md` for the source-controlled feature model.

## Validation

Repository CI renders `deploy/compose.yaml`, proves immutable-image enforcement, non-root/read-only/capability-free operation, external secret use, private networks, disabled multi-target scraping and `CONFIG`, no inline credential, and no public port publication.

A future approved deployment may use:

```bash
cp .env.example .env
# Set an accepted image digest and provision the external runtime secret.
docker compose -f deploy/compose.yaml config
docker compose -f deploy/compose.yaml up -d
# From the private observability network:
curl --fail http://redis-exporter:9121/metrics
```

Those commands are documentation only during the repository-first phase. Before target activation, later evidence must prove `redis_up == 1`, private-only reachability, no `/scrape` endpoint, no inline credential, bounded samples, required labels, ACL denial of prohibited commands, and rollback.

## Promotion and safety

Promotion is `feature/* -> development -> test -> staging -> production -> main`. Merging changes source authority only and does not deploy. `DEPLOYMENT_ENABLED=NO` remains binding until the 14-repository release manifest is accepted.
