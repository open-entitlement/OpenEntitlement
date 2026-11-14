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

Both Compose examples bind the published port to `127.0.0.1` and default
`OE_APP_URL` to `http://localhost:8787`, with `OE_OIDC_LOCAL_HTTP=true` for
local development. The service still rejects HTTP app or issuer origins outside
loopback. An HTTPS issuer works with this local HTTP console. Register the exact
`http://localhost:8787/auth/callback` redirect with your issuer. A loopback issuer
URL must be reachable from inside the container too; the host's localhost is not
the container's localhost.

For a TLS deployment, set `OE_APP_URL=https://console.example.com` and
`OE_OIDC_LOCAL_HTTP=false`, use an HTTPS issuer and register
`https://console.example.com/auth/callback`. Terminate TLS at a reverse proxy
that can reach the published loopback port. HTTPS app origins produce Secure
session cookies; HTTP local development cookies are not Secure.

The Python switch-over currently lacks the previous contract records, private PDF
upload/download and evidence-linking API and Organization panel. This is an
outstanding parity blocker, not a removal of that capability from the product.
Do not use the preview as a replacement for a deployment relying on those features.
