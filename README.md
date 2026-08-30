# Codestra Redis Exporter

This repository is the service authority for Redis availability, memory, persistence, replication, command, connection, eviction, latency, error, and keyspace infrastructure metrics. `appolon1908-hue/Codestra-Prometheus` owns scraping, canonical labels, recording rules, alerts, SLO evaluation, and retention.

## Least-privilege runtime

The exporter runs as a non-root user with a read-only filesystem, no Linux capabilities, `no-new-privileges`, and no host port. It joins only the private observability and cache networks. Prometheus reaches `redis-exporter:9121/metrics`; `rdex.codestra.media` is an ownership/DNS identifier and does not authorize a public endpoint, Caddy/Kong route, or Docker `ports:` mapping.

One exporter process owns exactly one deployment-controlled `REDIS_ADDR`. Both runtime candidates pass `--disable-scrape-endpoint`, so clients cannot select an arbitrary Redis target or inject `check-keys`, `check-single-keys`, streams, or count-key scans through `/scrape` query parameters. The runtime also disables key-value export, client-list export, client-port labels, the Redis `CONFIG` command, and TLS verification bypass.

## Password-map contract

The exact upstream exporter does **not** accept a raw password in `--redis.password-file`. It parses that file as a JSON object and looks up the normalized target URI, including the configured Redis ACL user.

For:

```text
REDIS_ADDR=rediss://redis.internal:6379
REDIS_MONITOR_USER=codestra_monitor
```

OpenBao must render the external secret as:

```json
{
  "rediss://codestra_monitor@redis.internal:6379": "INJECT_FROM_OPENBAO"
}
```

The runtime secret must contain exactly one target and one non-empty password. It may not contain a raw scalar password, additional targets, credentials embedded in `REDIS_ADDR`, line breaks, or an unapproved URI. The secret is mounted read-only at `/run/secrets/redis_password_map.json`; it is never copied into environment variables, Git, logs, metrics, or CI output.

Before any approved runtime action, validate the exact rendered password-map file:

```bash
python3 scripts/validate_runtime_password_map.py \
  --password-map /run/codestra/redis-exporter-password-map.json \
  --redis-addr "$REDIS_ADDR" \
  --redis-user "$REDIS_MONITOR_USER"
```

## Redis ACL

The monitoring ACL must permit only the commands required by the reviewed exporter version for connection health and read-only server statistics. It must not permit writes, scripting, module administration, replication administration, ACL changes, key reads, key scans, or destructive commands.

## Corporate metric and privacy contract

The corporate profile covers memory pressure, clients, commands, keyspace aggregate counts, evictions, replication, persistence, latency, blocked clients, and exporter errors across approved Redis instances. It uses controlled business/application/environment/deployment attribution while forbidding key names, values, scripts, customer data, session contents, raw payloads, and high-cardinality client-port labels.

See `codestra/enterprise-profile.v1.json` and `codestra/docs/CORPORATE-FEATURES.md` for the source-controlled feature model.

## Validation

Repository CI:

- builds and tests the exact locked upstream source;
- proves `--disable-scrape-endpoint` and `--redis.password-file` support;
- re-runs whenever upstream source, submodule metadata, or source-lock files change;
- renders both runtime candidates;
- proves non-root/read-only/capability-free operation, private networks, and no public port publication;
- validates the one-target JSON password map and rejects raw or multi-target files;
- rejects inline credentials and mutable image examples.

A future approved deployment may render the candidate only after the exact image, target, ACL, password map, private networks, and rollback packet are reviewed. No `docker compose up`, Redis ACL mutation, secret installation, or Prometheus target activation is authorized by this repository work.

Before Prometheus target activation, later staging evidence must prove `redis_up == 1`, private-only reachability, `/scrape` returns not found, no inline credential, bounded samples, required labels, ACL denial of prohibited commands, password-map rotation, and rollback.

## Promotion and safety

Promotion is `feature/* -> development -> test -> staging -> production -> main`. Merging changes source authority only and does not deploy. `DEPLOYMENT_ENABLED=NO` remains binding until the corporate-suite source and staging reviews are separately accepted.
