---
name: backend-boundary-testing
description: Use when changes cross frontend-to-backend, route-handler-to-service, auth/session, parser, permission, proxy, webhook, queue, or external HTTP boundaries.
---

# Backend Boundary Testing

## Purpose

Catch contract drift at the exact boundary that changed instead of relying only on broad end-to-end tests.

## When To Use

- Frontend route/action/proxy calls a backend API.
- Client fetcher or parser consumes backend JSON.
- Auth, session, cookie, token refresh, or logout behavior changes.
- Backend route, handler, service, webhook, queue consumer, or external integration changes.
- Permissions, tenancy, ownership, or policy checks change.

## Inputs

- Changed files.
- Canonical route, method, event, or contract.
- Expected auth, permission, and status behavior.
- Nearest existing tests for the same boundary type.

## Procedure

1. Map the changed boundaries.
2. Extend the nearest existing tests instead of creating a parallel harness.
3. Cover every changed boundary with at least one negative path.
4. Run focused tests for the touched boundary.
5. Summarize what was covered and what residual risk remains.

## Boundary Checklist

### Frontend Proxy Or Route Boundary

- auth required
- permission required
- params and body validation
- canonical upstream method and path
- safe `4xx` propagation
- unsafe `5xx` stripping

### Fetcher Or Parser Boundary

- URL and query construction
- response payload treated as unknown
- malformed payload rejection
- empty, unavailable, and error states
- structured client errors preserved where intended

### Auth Or Session Boundary

- unauthenticated vs unauthorized behavior
- stale or duplicate cookie precedence
- refresh, revoke, and logout behavior
- request-scoped session isolation
- no cross-user leakage

### Backend HTTP Or Event Boundary

- route or event is registered
- permission policy is correct
- params map into service calls correctly
- validation failures return expected errors
- not found and internal failure semantics are distinct

## Guardrails

- Do not add a new test framework for one boundary test.
- Do not cover only the happy path.
- Do not blur `401`, `403`, `404`, and `500` behavior.
- Do not let malformed input pass deeper than the earliest owning validator.
- Do not rely on browser-only tests when a focused parser, handler, or service test would prove the contract directly.

## Validation Checklist

- Every changed boundary has at least one focused test.
- Every changed boundary has at least one negative-path assertion.
- Auth and permission semantics are distinct when both are possible.
- Generated contracts and tests agree.
- Focused tests were run and reported.
