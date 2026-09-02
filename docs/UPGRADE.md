# Upgrade and upstream synchronization

Resolve the upstream tag to an exact commit and image index digest. Record the platform digest and binary revision output, attempt upstream signature/provenance verification, scan the exact image, and update both Compose sources and the runtime lock together. Re-run upstream tests, password-map tests, `/scrape` denial, ACL safety, metric cardinality and private-exposure validation. Promote protected commits only and retain a pullable previous digest/config artifact/checksum.
