# OPE-45 switch-over work record

Status: incomplete implementation; integration preview, not a released Python runtime.

Recovered the failed Opus implementation without modifying its checkout. The closing
branch starts at service/python 81db393 and merges main with no content changes:
OPE-70 already incorporated that main content and its integration fixes must remain.

Recovered slices:

- Python console security headers and opt-in public telemetry configuration, with HTTP
  and startup tests.
- Postgres restart/session persistence and idle connection recovery HTTP regression.
- React model imports moved into the web tree; temporary re-exports keep the old Node
  paths usable until retirement is complete.

Still required: Python publication and container smoke tests with a Product-scoped
SDK client; Compose and launch switch; Product quickstart and fresh-clone output;
Node retirement and black-box parity coverage; browser, Storybook, both SDK
conformance and Postgres validation; documentation and PRD delivery status updates;
whole-diff Spec/Standards review by the conductor.

Pending decisions from the conductor's new question batch (RFC-0006 and retaining
inert read-only defaults) are not answered by ADR-0010's older fourteen approvals.
Preserve current Python behavior until those answers are recorded. Do not mark
OPE-45 Done or change a protocol contract based on this recovery.

Local recovery checks: console typecheck passed; targeted Python startup/HTTP/restart
suite: 32 passed, 4 skipped (Postgres was not configured), one Starlette deprecation
warning; service Ruff passed. No local image verification: Docker pulls unavailable
per the task brief. Full delivery validation remains owed.
