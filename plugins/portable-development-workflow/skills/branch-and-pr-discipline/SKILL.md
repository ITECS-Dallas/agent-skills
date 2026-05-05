---
name: branch-and-pr-discipline
description: Use when starting code or docs work, checking git state, creating branches, staging files, committing, pushing, opening pull requests, or deciding whether a merge is authorized.
---

# Branch And PR Discipline

## Purpose

Keep changes reviewable, scoped, and recoverable.

## Guardrails

- Check `git status --short --branch` before substantive work.
- Inspect the whole worktree before commit, push, release, or handoff.
- Do not stage unrelated user changes silently.
- Do not commit directly to the default branch unless the user explicitly asked for a direct push or the repo is a new seed repo where that is the intended initial publish path.
- Use focused branches for normal feature work.
- Merge only when explicitly requested in the current session.
- Prefer squash merge unless the repo policy says otherwise.
- If the worktree becomes dirty from another actor during your task, inspect and coordinate instead of overwriting.

## Procedure

1. Inspect branch, remotes, and dirty state.
2. Decide whether the current branch is appropriate.
3. Create a branch with a clear name when feature isolation is needed.
4. Implement scoped changes.
5. Run relevant validation.
6. Stage only intended files.
7. Commit with a short imperative message.
8. Push with upstream tracking.
9. Open or update a PR when the workflow calls for review.

## Dirty Worktree Handling

- If dirty files are clearly part of the current task, include them intentionally.
- If dirty files are unrelated, stop and isolate or ask before staging.
- If dirty files are from a concurrent actor and affect the same files, read them carefully and work with them.
- Never use destructive reset or checkout commands unless explicitly requested.

## Validation Checklist

- Branch and dirty state were inspected.
- Staged files match the intended scope.
- Validation was run or the gap was explained.
- Commit message is focused.
- Push target is the intended remote and branch.
- No merge happened without explicit authorization.
