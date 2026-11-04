---
name: no-fallbacks
description: Use when a proposed fix may add silent defaults, compatibility shims, alternate providers, best-effort parsing, mock runtime data, retry masking, or temporary branches.
---

# No Fallbacks

## Purpose

Prevent broken behavior from being hidden by silent fallbacks or permanent temporary paths.

## Default Rule

Fail fast, expose the real problem, and fix the root cause.

## Disallowed By Default

- Silent default config when required env is missing.
- Alternate provider chains that hide integration failure.
- Best-effort parsers that accept invalid contract payloads.
- Runtime mock data on shipped paths.
- Compatibility aliases without an explicit live caller and removal plan.
- Catch-all retries that hide deterministic failures.
- Temporary branches with no owner, deadline, or validation.

## Allowed Only When Explicitly Bounded

A fallback or compatibility path may be acceptable when all are true:

- The user or project policy explicitly requires it.
- The exact current caller or migration constraint is named.
- The behavior is version-gated or feature-gated where appropriate.
- The removal condition is documented.
- Tests cover both old and new paths.

## Procedure

1. Identify the failure the fallback would hide.
2. Trace the root cause.
3. Replace the fallback with a direct fix when possible.
4. If compatibility is required, make the boundary explicit and temporary.
5. Add validation that would fail if the root cause returns.

## Final Summary Requirement

State whether any fallback, shim, alias, or temporary path remains. If one remains, state why, where, and how it is removed.
