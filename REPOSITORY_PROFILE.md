# Repository Profile — `Codestra-Redis-Exporter`

## Identity

- **Repository:** `appolon1908-hue/Codestra-Redis-Exporter`
- **Category:** Observability exporter — Redis
- **Visibility:** `public`
- **Default branch:** `main`
- **Canonical hostname:** `rdex.codestra.media`
- **Exposure:** Internal/private only; no public multi-target scrape endpoint
- **Authority:** Primary safe aggregate Redis availability, memory, client, eviction, latency, replication, RDB, and AOF metrics authority

## Purpose

Exports bounded Redis infrastructure health to Prometheus using one approved exporter identity per Redis instance/role without exposing keys, values, client data, or credentials.

## Owns

- Redis Exporter runtime, approved aggregate metric scope, and role taxonomy
- Read-only Redis monitoring ACL contract and secret-file boundary
- Instance/business labels, health, immutable packaging, and private-network source

## Does not own

- Redis application data or key/value inspection
- Public `/scrape` multi-target behavior
- Redis mutation, configuration changes, or business/financial authority

## Key integrations

- Approved Redis instances
- Prometheus
- Grafana and Alertmanager
- OpenBao/runtime secret delivery where adopted

## Current priorities

1. Maintain one exporter per approved Redis instance and role
2. Prove exact password-file handling, read-only ACL behavior, and private networking
3. Validate memory, eviction, blocked-client, replication, latency, RDB, and AOF alerts
4. Add immutable packaging, upgrade, rollback, and credential-rotation evidence

## Governance and safety

- Promotion model: `feature/docs/fix/security/upgrade -> development -> test -> staging -> production -> main`.
- Native port `9121` must remain private; `rdex.codestra.media` must not expose metrics publicly.
- Never commit Redis passwords, URIs with credentials, keys, values, client lists, customer data, or private keys.
- Monitoring ACLs must remain read-only and narrowly scoped.
- Merge does not create Redis ACLs, install passwords, start the exporter, activate scraping, or expose ports.

## Account-wide catalog

See `appolon1908-hue/documentaions/REPOSITORY_CATALOG.md`.
