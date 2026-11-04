---
name: dependency-reuse
description: Use when deciding whether to reuse, extend, replace, upgrade, or add helpers, wrappers, adapters, scripts, dependencies, generated surfaces, fixtures, or test utilities.
---

# Dependency Reuse

## Purpose

Make reuse and simplification the default. Add new dependencies or helpers only after existing options have been checked and rejected for a concrete reason.

## Decision Order

1. Language or runtime built-ins.
2. Existing repo helper, module, script, or test utility.
3. Already-present dependency or installed tool.
4. Maintained external dependency.
5. Custom helper or script as the last resort.

## Procedure

1. Search the repo for similar helpers, utilities, scripts, and patterns.
2. Inspect manifests and lockfiles.
3. Check nearby tests and generated surfaces.
4. Decide using the order above.
5. If adding a dependency or helper, document why reuse was insufficient.
6. If replacing an old helper, update callers and remove the superseded path when safe.

## Guardrails

- Do not add thin wrappers that only rename an existing abstraction.
- Do not duplicate generated DTOs by hand.
- Do not create a one-off script when a repo script or standard tool already solves the problem.
- Do not preserve old and new paths in parallel unless a migration constraint is explicit and bounded.
- Prefer improving the existing abstraction over creating a parallel one.
- Prefer removing unnecessary dependencies over upgrading unused ones.

## Final Summary Requirement

When custom code or a new dependency is added, state:

- what you searched
- what existed
- why reuse was not enough
- why the new dependency or helper is appropriate
