---
name: is-it-good-enough
description: Use when evaluating whether a code or docs change is minimal, correct, tested, maintainable, free of fallback layers, and ready for handoff, commit, PR, or release review.
---

# Is It Good Enough

## Purpose

Run a final adversarial quality gate before claiming the work is done.

## Review Questions

- Does the change satisfy the actual acceptance criteria?
- Is the diff smaller than a rewrite and large enough to fix the root cause?
- Did it preserve existing repo patterns?
- Did it avoid fallback layers, compatibility shims, and speculative abstractions?
- Are validation checks proportional to the risk?
- Did tests cover negative paths and changed boundaries?
- Are docs updated where behavior changed?
- Are secrets, env values, and private paths absent from the diff?
- Is any production, data, billing, or security action still awaiting approval?

## Procedure

1. Inspect the full diff.
2. Compare the diff to the acceptance criteria.
3. Check for unnecessary new dependencies, helpers, wrappers, and broad rewrites.
4. Check changed boundaries for focused tests.
5. Check docs parity.
6. Run or confirm relevant validation.
7. Summarize:
   - ready or not ready
   - what proves it
   - remaining risk

## Not Ready Signals

- The fix works only because of a fallback path.
- Tests cover only the happy path.
- Generated files were hand-edited.
- A stale doc still contradicts the code.
- The diff includes unrelated cleanup.
- The implementation depends on a local path, secret, or machine-specific assumption.
