---
name: pragmatic-delivery
description: Use when scope, implementation size, cleanup, refactor depth, release readiness, or follow-up boundaries need to be kept practical and tied to the requested outcome.
---

# Pragmatic Delivery

## Purpose

Ship the smallest durable change that solves the real problem.

## Principles

- Start from the current repo shape.
- Preserve working patterns unless there is a concrete reason to change them.
- Fix the owning layer, not every related smell.
- Prefer direct changes over speculative abstraction.
- Add tests where risk changed.
- Leave unrelated cleanup for follow-up work.

## Procedure

1. Convert the request into acceptance criteria.
2. Identify the owning files and boundaries.
3. Implement the direct fix.
4. Remove superseded code when the replacement is complete.
5. Run the nearest useful validation.
6. Record follow-up work only when it is real and not required for this change.

## Scope Control

Do not broaden the task just because you see:

- neighboring style inconsistencies
- outdated dependencies unrelated to the fix
- old tests that are not on the changed path
- documentation gaps outside the changed behavior
- alternate architecture that would require a larger migration

## Done Means

- Acceptance criteria are met.
- Validation is credible for the risk.
- The diff is focused.
- Handoff names remaining risk clearly.
