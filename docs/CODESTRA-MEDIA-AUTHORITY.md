# Codestra Redis Exporter Authority

Principal repository: `appolon1908-hue/Codestra-Redis-Exporter`
Canonical service host: `rdex.codestra.media`
Canonical DNS target: `37.27.128.39`
TTL: `600`

DNS has been externally verified. No alternate authoritative hostname is permitted.

## Ownership
Own Redis Exporter deployment/configuration, least-privilege monitoring connection policy, metric exposure validation and upgrade runbooks. Do not own Redis application configuration, Prometheus scrape policy, Grafana dashboards, Caddy or secrets.

## Exposure
Private/internal only. DNS may exist, but exporter ports must be restricted to Prometheus/private monitoring networks.

## Integration
Upstream: approved Redis instances using monitoring-only credentials. Downstream: Prometheus scrapes.

## Branch policy
Persistent: `main`, `development`, `test`, `staging`, `production`.
Temporary: `feature/*`, `fix/*`, `upgrade/*`, `security/*`, `docs/*`, `hotfix/*`, optional `release/*`, `rollback/*`.
Promotion: work -> development -> test -> staging -> production -> main.
