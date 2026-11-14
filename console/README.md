# React console and Python service

The React console stays TypeScript. The service runs with uv and Python; the Node
service has been retired (ADR-0009). `npm start` launches the Python service.

Follow the [Product quickstart](../website/src/content/docs/docs/quickstart.md)
for local sign-in and a Product-scoped SDK evaluation. See the
[service guide](../sdk-python/packages/service/README.md) for settings, migrations,
OIDC and repository tests. Build the console with `npm ci && npm run build` here.

Validation: `npm run typecheck`, `npm test`, `npm run build:storybook`,
`npm run test:storybook`. `OE_PG_DSN=… npm run test:python-service` runs the
black-box Chromium parity suite with real OIDC and a disposable Postgres database.
The same suite accepts `OE_TEST_IMAGE` to run the published container runtime
on a Docker host supporting host networking.
