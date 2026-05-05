---
name: project-development-workflow
description: Use when implementing, debugging, or refactoring application code and the work may involve frontend, backend, API contracts, repo boundaries, docs, tests, or PR handoff.
---

# Project Development Workflow

## Purpose

Route normal coding work through the smallest useful set of skills without assuming a specific stack or repo layout.

## When To Use

- Feature, bugfix, refactor, or test work in an application repo.
- Work that may cross frontend, backend, API, auth, storage, or integration boundaries.
- Handoff prompts for another coding agent.
- Final readiness checks before commit, push, PR, deploy handoff, or release handoff.

## Inputs

- User goal and acceptance criteria.
- Current repo root and local instruction files.
- Touched areas, if already known.
- Available validation commands.

## Required Local Discovery

Before coding, inspect project-local instructions first:

- `AGENTS.md`
- `CLAUDE.md`
- `.cursor/rules`
- `README.md`
- package manifests, Makefiles, compose files, CI configs, and test docs relevant to the touched area

Treat project-local docs as the source for local commands and environment boundaries. Treat this skill as a reusable workflow overlay.

## Routing

Classify the work:

| Work Type | Load These Skills |
| --- | --- |
| Frontend only | `frontend-app-dev`, `dependency-reuse`, `no-fallbacks`, `pragmatic-delivery` |
| Backend/API only | `backend-api-dev`, `dependency-reuse`, `no-fallbacks`, `pragmatic-delivery` |
| Frontend-to-backend boundary | `frontend-app-dev`, `backend-api-dev`, `backend-boundary-testing`, `dependency-reuse`, `no-fallbacks`, `pragmatic-delivery` |
| Branch, commit, push, PR | `branch-and-pr-discipline` |
| Behavior or public docs changed | `docs-parity` |
| Unclear repo ownership | `repo-boundaries` |
| Final implementation review | `is-it-good-enough` |
| Selecting test scope | `testing-gates-and-harnesses` |

## Procedure

1. Confirm the current repo, branch, and dirty state.
2. Read local project instructions and identify the owning surface.
3. Name the correct local pattern to preserve.
4. Name the anti-patterns to avoid in the touched path.
5. Implement the smallest direct change that satisfies the acceptance criteria.
6. Add or update tests at the boundary that changed.
7. Run targeted checks first, then broader checks when risk justifies them.
8. Run `is-it-good-enough` before handoff for code edits.
9. Summarize changed files, validation, and remaining risk.

## Guardrails

- Do not invent project commands when local docs provide them.
- Do not add fallback branches or compatibility layers unless the user explicitly approves a bounded migration.
- Do not introduce helpers, wrappers, or dependencies until existing options have been checked.
- Do not let generic skill guidance override project-specific security, deployment, or approval boundaries.
- If a production, data, billing, security, or customer-impacting action is required, stop at the correct approval boundary.

## References

- `frontend-app-dev/SKILL.md`
- `backend-api-dev/SKILL.md`
- `backend-boundary-testing/SKILL.md`
- `dependency-reuse/SKILL.md`
- `no-fallbacks/SKILL.md`
- `pragmatic-delivery/SKILL.md`
- `is-it-good-enough/SKILL.md`
