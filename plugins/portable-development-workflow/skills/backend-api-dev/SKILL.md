---
name: backend-api-dev
description: Use when changing backend API code, route handlers, service logic, auth or permission checks, data models, migrations, generated contracts, seeds, streaming endpoints, or integration boundaries.
---

# Backend API Dev

## Purpose

Implement backend changes with contract-first routing, explicit data ownership, focused tests, and safe operational boundaries.

## Read First

Open local project guidance before editing:

- backend `README.md`
- API contract docs
- migration and seed docs
- service boundary docs
- test and local runtime docs
- deployment or production safety notes when runtime behavior is affected

## Guardrails

- Contract first: update canonical API schemas before generated handlers or clients.
- Validate input at the earliest owning boundary.
- Keep auth failures distinct: unauthenticated is `401`, unauthorized is `403`.
- Preserve `404` semantics for missing resources and avoid leaking resource existence when the project policy requires concealment.
- Do not hide missing config, broken integrations, or schema drift with fallback behavior.
- Keep data migrations and destructive data operations behind the project's explicit approval gates.
- Prefer existing service, repository, transaction, and test patterns.
- Do not add a new abstraction when updating the existing one is clearer.

## Procedure

1. Identify the owning module and boundary.
2. Find the canonical contract: OpenAPI, GraphQL schema, protobuf, typed RPC schema, route table, or local API docs.
3. Update contract and generated surfaces in the order the repo expects.
4. Implement handler, service, persistence, and integration changes in the owning layer.
5. Add focused tests:
   - route registration
   - auth and permissions
   - input validation
   - service behavior
   - persistence or transaction behavior when touched
   - integration boundary behavior when touched
6. Run targeted backend tests, then broader suites when shared contracts or runtime startup changed.
7. Document any required migration, env var, release, or operator action.

## Data And Migration Safety

- Inspect existing migration conventions before adding files.
- Prefer reversible or forward-safe changes when supported by the stack.
- Do not run live migrations from a local coding environment unless the user explicitly authorizes that production action.
- Keep seed data deterministic and clearly separated from production data.
- If a migration requires backfill, lock, downtime, or operator coordination, stop at a handoff plan.

## Validation

Choose commands from local docs. Common examples:

- backend unit tests for touched packages
- route/handler tests
- contract generation and drift checks
- migration dry-run or syntax validation
- containerized integration tests when startup wiring changed

## References

- `backend-api-dev/references/module-map.md`
- `backend-api-dev/references/codegen-targets.md`
- `backend-boundary-testing/SKILL.md`
- `dependency-reuse/SKILL.md`
- `no-fallbacks/SKILL.md`
