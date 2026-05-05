---
name: repo-boundaries
description: Use when work may cross repository, package, service, generated-code, deployment, data, security, or ownership boundaries and the correct place to change behavior is unclear.
---

# Repo Boundaries

## Purpose

Change the owning system instead of patching around it from the wrong layer.

## Boundary Types

- Frontend vs backend.
- Public API vs internal service.
- Generated code vs generator input.
- Runtime config vs source code.
- Local development vs production operations.
- Data migration vs application code.
- Shared package vs app-specific wrapper.
- Project-local guidance vs global skill guidance.

## Procedure

1. Identify the behavior owner.
2. Identify generated surfaces and their sources.
3. Identify local commands and approval gates.
4. If multiple repos are involved, map the contract and handoff order.
5. Change the canonical owner first.
6. Update consumers and docs in the same branch when feasible.
7. Stop before production, data, or security actions that need explicit approval.

## Guardrails

- Do not hand-edit generated code when the generator input is available.
- Do not implement backend-owned aggregation in a frontend-only patch.
- Do not change production env, database, or infrastructure from a coding checkout unless explicitly authorized.
- Do not let global skills override project-local instructions.
- Do not assume sibling repos exist; discover them.

## Output

Summarize:

- owning boundary
- files changed
- generated surfaces updated
- commands run
- any cross-repo or operator follow-up
