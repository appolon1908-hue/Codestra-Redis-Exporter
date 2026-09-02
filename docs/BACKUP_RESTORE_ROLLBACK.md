# Recovery and rollback design

Redis Exporter is stateless. Redis data recovery belongs to the Redis authority. This repository recovers only the signed configuration bundle, exact runtime image digest, private-network mapping and secret reference names.

Before a change, record the protected source SHA, exact image/config digests, checksum, private network identities, secret-file presence without values, approved target and `redis_up`. Retain the previous pullable artifacts. Validate restore on an isolated Redis instance with an ephemeral least-privilege ACL: require `/metrics`, `redis_up == 1`, `/scrape` denial, prohibited command denial, bounded labels and no host port.

Rollback uses the actual previous image/config digests and checksum as one reviewed unit. If exporter flags or password-map format are incompatible, use forward recovery. Repository tests are not production backup, restore or rollback evidence.
