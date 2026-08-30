# Codestra Redis Exporter Corporate Features

## Mission

Redis Exporter provides safe aggregate health metrics for Redis instances used by Codestra-managed applications. It supports cache, session, queue and worker troubleshooting without exposing Redis data values.

## Required coverage

Track memory use, connected/blocked clients, commands, aggregate keyspace size, expirations, evictions, replication, persistence, latency and errors.

## Corporate features

- multiple Redis instance monitoring with safe instance/business metadata;
- memory-pressure and maxmemory alerts;
- unexpected eviction detection;
- replication link/lag health;
- RDB/AOF persistence failure visibility where used;
- blocked-client growth detection;
- latency and command-rate trends;
- aggregate keyspace growth;
- correlation with application queue/backlog metrics;
- Grafana business/service drill-down.

Application-level queue depth remains an application metric; Redis internals alone are not treated as the authoritative workflow backlog.

## Privacy/security

Never export Redis key values, customer payloads, tokens, session contents or other stored business data. Redis credentials are injected from OpenBao or approved runtime secret files. `rdex.codestra.media` and the exporter listener remain private and are scraped by Prometheus over approved network paths.

## Release rule

Codestra configuration stays outside imported upstream source. Merge does not enable deployment or Redis access.
