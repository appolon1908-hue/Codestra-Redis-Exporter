# Security policy

Report vulnerabilities through GitHub Security Advisories without production credentials or customer data. Redis Exporter must remain non-root, read-only, capability-free and private.

The scrape endpoint for caller-selected targets, key/value export, client-list export, client-port labels, `CONFIG`, TLS verification bypass, public port publication and credentials in environment values are forbidden. The only credential input is the reviewed one-target password-map file rendered by the secrets authority. Source changes do not create an ACL, read Redis or deploy the exporter.
