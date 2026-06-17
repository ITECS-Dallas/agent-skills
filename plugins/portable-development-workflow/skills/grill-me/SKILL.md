---
name: grill-me
description: Use when the user asks to be grilled, interviewed, challenged, or walked through decisions for a plan, remediation path, feature, migration, workflow, or ambiguous implementation.
---

# Grill Me

## Purpose

Drive an ambiguous plan to shared understanding by resolving decisions one at a time. Ask only for human judgment; answer discoverable facts by inspecting the codebase, docs, data, or configured tools first.

## Required Flow

1. Restate the goal and list the concrete issues or branches you see.
2. Build a decision tree mentally: user outcome, current behavior, desired behavior, data model, UI copy, permissions, edge cases, rollout, validation, and docs parity.
3. Explore first for any question the repository, docs, app, logs, screenshots, or tools can answer.
4. Ask exactly one unresolved question at a time.
5. For every question, include a recommended answer and a brief reason.
6. Wait for the user's answer before asking the next question.
7. Track resolved decisions and dependencies as the interview progresses.
8. Stop grilling when the remaining path is specific enough to produce an implementation plan with acceptance criteria and validation gates.

## Question Format

```text
Question: <one decision that needs human judgment>

Recommended answer: <your recommendation>

Reason: <why this choice best fits the goal and constraints>
```

If useful, add a short "Already verified" line before the question with code or docs facts that removed nearby questions.

## What To Ask

- Product intent: what the user must understand or accomplish.
- Scope: what is in, out, deferred, or intentionally unchanged.
- UX contract: labels, sequence, confirmation steps, error states, and back-button behavior.
- Data contract: fields, source of truth, privacy boundaries, and persistence.
- Operational contract: billing, auth, emails, logs, webhooks, admin review, and rollback.
- Validation: exact tests, browser checks, screenshots, and docs updates needed before handoff.

## What Not To Ask

- Do not ask questions that can be answered with repository exploration.
- Do not batch multiple questions unless the user explicitly asks for a questionnaire.
- Do not ask vague preference questions without a recommended answer.
- Do not move into implementation until the decision tree has no material unresolved branch.
