---
name: frontend-app-dev
description: Use when changing frontend application code, routes, components, hooks, API proxies, auth/session reads, rendering behavior, generated client types, UI tests, or performance-sensitive client boundaries.
---

# Frontend App Dev

## Purpose

Implement frontend changes with repo-native patterns, typed contracts, narrow client boundaries, and honest runtime behavior.

## Read First

Open local project guidance before editing:

- frontend `README.md`
- app framework docs in the repo
- route or component docs near the touched files
- generated-type or API-client instructions
- test setup docs

If local guidance conflicts with this skill, follow the local guidance and document the reason.

## Guardrails

- Keep secrets server-side. Browser code should use same-origin routes or server actions when tokens, cookies, or privileged headers are involved.
- Treat backend responses as `unknown` until parsed or validated.
- Prefer generated API types over handwritten mirrors.
- Do not add silent fallback UI for broken contracts. Show an explicit unavailable/error state or fix the contract.
- Do not widen client-only scope unless browser APIs, local state, or event handlers require it.
- Avoid calling same-origin API routes from server-rendered code when a server-only data helper can call the backing service directly.
- Keep route, cache, and data freshness choices explicit.
- Use existing design system components and existing test harnesses before adding new ones.

## Contract Workflow

1. Identify the backing API or data source.
2. If the API contract changed, update the canonical spec first.
3. Regenerate client types with the project's existing generator.
4. Update fetchers, parsers, and route handlers together.
5. Add focused tests for changed parsing, auth, status, and error behavior.
6. Run targeted frontend checks, then broader checks when shared shell or routing changed.

## Server-Only Auth Pattern

- Tokens and privileged cookies stay in server-only helpers.
- Client components call same-origin routes or actions.
- Same-origin proxy routes validate method, auth, params, body, and upstream status.
- Unsafe upstream details are stripped from user-facing `5xx` responses.
- Safe `4xx` details may be preserved when they are part of the public contract.

See `references/server-only-auth.md` for a generic route-handler pattern.

## Performance Checks

- Prefer server-rendered static structure and narrow interactive islands.
- Add loading boundaries for dynamic or slow routes.
- Avoid adding large client libraries to shared shells without measurement.
- For image, font, or route changes, verify layout stability and first meaningful render.

See `references/performance.md` for a checklist.

## Validation

Select commands from local project docs. Common examples:

- typecheck
- lint
- unit tests for touched components/hooks/routes
- integration or browser tests for changed user flows
- production build when routing, framework config, or shared shell changed

## References

- `backend-boundary-testing/SKILL.md`
- `dependency-reuse/SKILL.md`
- `no-fallbacks/SKILL.md`
- `frontend-app-dev/references/codegen.md`
- `frontend-app-dev/references/server-only-auth.md`
- `frontend-app-dev/references/performance.md`
