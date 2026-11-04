---
name: codex-prompting-style
description: Use when writing implementation prompts, handoff prompts, or coding-agent instructions for features, bug fixes, refactors, tests, verification, or repo maintenance.
---

# Codex Prompting Style

## Purpose

Make coding-agent prompts executable, bounded, and verifiable.

## Prompt Shape

Use this structure for implementer handoffs:

```text
You are an autonomous coding agent. Implement the requested change end-to-end.

Goal:
- <one sentence>

Non-negotiable acceptance criteria:
- [ ] <criterion>
- [ ] <criterion>

Repo/workdir:
- <path or repo root>

Key files to inspect first:
- <file or directory>

Constraints:
- Keep changes minimal and scoped.
- Prefer existing repo patterns.
- Fix the root cause.
- Do not add fallback branches, compatibility shims, or speculative abstractions unless explicitly required.
- Modify only files inside the target workdir unless the task explicitly says otherwise.
- Ask only blocking questions.

Validation:
- Run: <command>
- Run: <command>

Output:
- Summarize changed files, validation results, and remaining risk.
```

## Guardrails

- Include concrete files, commands, and stop conditions.
- Do not request an upfront essay or plan unless planning is the deliverable.
- Avoid vague requests like "clean up" without acceptance criteria.
- Include the exact approval boundary for risky operations.
- Include repo-local source-of-truth docs when they matter.
- State whether the agent may commit, push, deploy, restart services, or mutate data.

## Validation

A good prompt lets another agent:

- find the repo
- understand the goal
- identify the owning files
- avoid scope creep
- run the right checks
- stop at the right boundary
- report useful evidence
