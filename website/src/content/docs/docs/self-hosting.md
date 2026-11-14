---
title: Self-hosting
description: Run the Python service with Postgres and your identity provider.
---

Build the current preview with `docker build -t openentitlement:local .`.
The image contains Python and the compiled React console, runs as an unprivileged
user, and checks `/healthz`. Node is used only to build the console.
The publication workflow tests the image before publishing `edge` or a tagged
release. Existing release tags retain their original runtime.

Use `deploy/compose.postgres.yaml` with `OE_VERSION`, `POSTGRES_PASSWORD`,
`OE_OIDC_ISSUER`, `OE_OIDC_CLIENT_ID`, `OE_PLATFORM_ADMIN_SUBJECT` and
`OE_APP_URL` supplied by your deployment. URL-encode the database password.
Migrations run at startup. Keep the Postgres volume backed up.

For an ephemeral API-only instance, `deploy/compose.memory.yaml` sets
`OE_IN_MEMORY=true`; configure OIDC to sign in. No demo seed or anonymous
administrative token is supported. Console sessions use OIDC; evaluation uses
API keys bound to a Product. Never send those keys to an untrusted browser.

See the repository's `sdk-python/packages/service/README.md` for the complete
settings and row-level-security requirements. Use TLS at the reverse proxy.
Telemetry is disabled unless explicitly enabled. Read-only evaluation does not
charge, allocate licenses or consume application quota.
