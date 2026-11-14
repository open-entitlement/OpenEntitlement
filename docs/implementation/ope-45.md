# OPE-45 switch-over work record

Status: integration preview; not complete or released. Current-head Linux image parity and
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

Python parity is implemented in `services/contracts.py`, the memory/Postgres
repository adapters, migration `0010_contracts`, and the Workspace Organization
panel. Contract metadata is a typed, versioned record; PDF bytes are stored
separately and never included in JSON, YAML configuration, audit snapshots or
OEREP responses. Contract dates and status remain documentary only.

Contracts belong to one Workspace, Product and Organization. Product Managers,
Workspace Owners and Platform administrators can manage/read these confidential
records; Product Users cannot read the embedded actor history or private PDFs.
Every operation checks this authority before reading records. Writes take the
same Product lock as Organization terms and application users; contract versions
protect metadata edits. PDF/history/evidence/audit writes commit together.

Evidence uses explicit service-value identities: `terms:<privilege>` names an
Organization term and `grant:<subject ID>:<privilege>` names an application-user
Grant, both in the contract's Product and Organization. These are control-plane
references, not new SDK IDs or protocol PDF fields. Source existence is checked
under the Product lock. Pages are positive safe integers referencing a PDF owned
by the contract; the prior implementation did not parse or verify page counts,
and this port does not invent extraction behavior.

The retained Organization contract panel now uses the authenticated session and
CSRF transport, including raw PDF uploads. Caller-supplied actors and admin tokens
are not used. Unified audit records capture authenticated actors and metadata
changes; the retained contract history also records actor email, reason and time.

No reduced-scope rollout, merge or release is established by this implementation.
Whole-integration conductor review and current-head Linux image parity remain
required before accepting OPE-45.

## Validation

See the PR finding response for commands/results pinned to the fixing head.
Required Linux image/browser/SDK parity and fresh conductor Spec/Standards review
are still owed. Prior implementation evidence is not a result for a new head.

Contract parity implementation validation (2026-11-14):

- Postgres-enabled `uv run pytest -q tests/service`: **466 passed**, one
  Starlette deprecation warning. Final focused contract/restart rerun after
  service-entry authorization hardening and metadata edit coverage: **7 passed**.
- Contracts cover memory and Postgres: foreign Workspace/Product/Organization,
  Product User/foreign Manager refusals, real audit actors, malformed/oversized
  PDFs, 20-document limit, term/Grant ownership, document/page references,
  concurrent uploads, stale edits, transaction rollback and restart persistence.
- Console typecheck, production build, **20 console tests**, real-OIDC browser
  contract upload/link/download and both SDK outputs pass. Reusable contract
  evidence story exercises source/PDF/page selection.
- Strict service mypy (**52 source files**), CI Ruff scope, three import-layer
  contracts, deptry and exact SDK npm quality command pass. Root Docker image
  rebuild passes; no dependency reintroduced into the console.
- Local image browser parity was attempted twice, including an all-interface
  container listener. Docker Desktop host networking still could not reach the
  service although migrations and internal health checks succeeded. Full Linux
  image/browser parity remains required; this is not a green container claim.
- Self-review: Spec retains metadata/history, private evidence, service-only
  references and documentary dates with no quota/billing/license effects.
  Standards checks typed validation, Product locks, record versions, Workspace
  RLS, transaction boundaries, CSRF and authenticated audit. This is implementer
  self-review, not independent approval. Conductor must review the whole diff.
