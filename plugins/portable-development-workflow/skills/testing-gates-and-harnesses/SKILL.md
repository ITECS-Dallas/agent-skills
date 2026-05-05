---
name: testing-gates-and-harnesses
description: Use when choosing validation for protocol changes, runtime regressions, permissions, live-stack readiness, browser flows, migrations, build output, smoke tests, or CI blockers.
---

# Testing Gates And Harnesses

## Purpose

Run tests that match the risk introduced by the change.

## Gate Selection

| Changed Area | Useful Gates |
| --- | --- |
| Pure function or helper | focused unit tests |
| Parser or contract | malformed payload tests, generated drift checks |
| Route handler | method, auth, validation, status, and upstream behavior tests |
| Frontend component | unit/component tests, browser flow for user-visible behavior |
| Shared shell or routing | production build, browser smoke, responsive checks |
| Backend service | package tests, integration tests where persistence changed |
| Migration | syntax check, dry-run, rollback/forward plan where supported |
| Auth or permissions | positive and negative permission tests |
| External integration | mocked boundary tests plus safe smoke if authorized |
| Release or runtime wiring | startup, health, and one representative user path |

## Procedure

1. Identify what risk changed.
2. Start with the nearest focused test.
3. Add boundary tests when a contract changed.
4. Run broader suites when shared behavior, routing, startup, or generated contracts changed.
5. If a check cannot run, explain the missing dependency or environment and provide the best substitute.

## Guardrails

- Do not rely on a production build as the only proof of business behavior.
- Do not rely on UI browser tests as the only proof of backend validation.
- Do not lower coverage gates to pass a PR.
- Do not skip negative paths for auth, permissions, parsers, or route handlers.
- Do not claim live readiness from local-only checks.

## Final Summary

List commands run, results, and residual untested risk.
