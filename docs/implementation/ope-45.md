# OPE-45 switch-over work record

Status: integration preview; not complete or released. Contract/PDF parity and
fresh conductor review remain required before accepting the switch-over.

The root `Dockerfile`, Compose examples and `npm start` now launch Python and
serve the compiled React Workspace console. The Node server and temporary model
re-exports are retired; shared browser models live under `console/web/src`.
The root Docker build installs the SDK workspace's locked dependencies in
`/app/sdk-js`, then the console's in `/app/console`; it does not borrow console
dependencies through a symlink. SDK source exports are compiled by Vite.

Product-bound quickstart and both SDK outputs are covered by the real-OIDC
browser regression, also run against the publication image in Linux CI.
Integration/security/browser fixes from OPE-70 remain part of this branch.
Read-only values remain inert and RFC-0006 remains proposed.

## Contract and private PDF parity blocker

The prior accepted implementation (#13, main's `console/server/contracts-api.ts`,
`contracts-store.ts`, `console/test/contracts.test.ts` and
`console/web/src/contracts.tsx`) supports:

- Create/list/read/update Organization contract metadata, external references,
  status and dates, with reasons and history; dates do not affect evaluation.
- Private PDF upload/download, 10 MiB and 20-document limits, PDF marker and type
  checks, SHA-256 metadata and attachment/no-store/sandbox download headers.
- Evidence links to existing Organization overrides or grants, optional PDF/page
  and notes, rejecting foreign sources/documents and invalid pages.
- Transactional metadata/PDF/history persistence, concurrent uploads and restart
  survival in Postgres; anonymous/evaluation credentials cannot access documents.
- An Organization panel for the complete flow.

Python has no corresponding tables/migration, repository protocols/adapters,
service operations or HTTP routes; WorkspaceApp does not mount ContractsPanel.
The legacy panel/types remain in source but do not establish runtime support.
This is substantial missing functionality, not a documentation-only discrepancy.
The old global admin-token API and caller-supplied actor cannot simply be mounted
in the authenticated Workspace service. Evidence IDs must map to current
Product-scoped Organization terms and application-user Grants. The implementation
must retain Workspace isolation and actual authenticated audit actors.

Concrete options for the conductor/owner:

1. Keep OPE-45 blocked while implementing Python contract/evidence repositories,
   Workspace/Product authorization, typed service operations and routes, private
   document storage and the Organization UI. Restore the prior regression matrix
   with cross-Workspace/Product refusals, authenticated audit, transactional
   concurrency/restart tests and a real-OIDC upload/link/download browser test.
2. Split the launch switch from the integration and keep the existing Node launch
   as the default until equivalent Python functionality passes that matrix.

Neither option removes the approved capability. No reduced-scope rollout is
approved here; the PRD retains its historical implementation and names the gap.
Do not mark OPE-45 Done or merge this switch-over on documentation changes alone.

## Validation

See the PR finding response for commands/results pinned to the fixing head.
Required Linux image/browser/SDK parity and fresh conductor Spec/Standards review
are still owed. Prior implementation evidence is not a result for a new head.
