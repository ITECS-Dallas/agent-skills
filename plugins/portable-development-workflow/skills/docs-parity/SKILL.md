---
name: docs-parity
description: Use when shipped behavior, public APIs, routes, configuration, architecture, runbooks, source-of-truth docs, generated contracts, or user-visible workflows change.
---

# Docs Parity

## Purpose

Keep canonical documentation aligned with the behavior being shipped.

## When To Use

- Public behavior changed.
- API contracts or generated clients changed.
- Run commands, release steps, or environment requirements changed.
- Architecture or ownership boundaries changed.
- User-facing or operator-facing workflows changed.
- A previous doc becomes misleading after the code change.

## Procedure

1. Identify the owning docs:
   - root README
   - project `AGENTS.md` or `CLAUDE.md`
   - architecture docs
   - API docs
   - runbooks
   - generated docs
   - test or release docs
2. Update only the docs that are authoritative for the changed behavior.
3. Remove or mark superseded docs when they would mislead future agents.
4. Keep examples executable and aligned with current commands.
5. Include docs validation in the final summary.

## Guardrails

- Do not duplicate source-of-truth content across many files.
- Do not update docs with aspirational behavior that did not ship.
- Do not leave stale commands next to new commands.
- Do not bury required operator actions only in PR prose when a runbook should own them.

## Validation Checklist

- The owning docs mention the new behavior.
- Stale references were removed or corrected.
- Commands in docs match current scripts.
- Any required migration, env var, or deploy action is documented.
