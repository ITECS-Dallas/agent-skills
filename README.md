# Agent Skills

Portable development workflow skills for Codex, Claude, and other coding agents.

This repo is the source of truth for reusable agent guidance. It is intentionally project-neutral: no skill assumes a company, product, filesystem path, repository name, cloud account, or local machine layout. Project-specific rules should stay in each project's `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, or equivalent local instruction file.

## What Is Included

- `plugins/portable-development-workflow/` - Codex plugin-ready bundle.
- `plugins/portable-development-workflow/skills/` - the reusable skill catalog.
- `scripts/install.sh` - copies or symlinks skills into local agent skill directories.
- `scripts/validate.mjs` - validates skill frontmatter, plugin metadata, and portability.
- `templates/project-skill-source-of-truth.md` - drop-in project docs for linking this repo from another project.

## Skill Catalog

| Skill | Use |
| --- | --- |
| `project-development-workflow` | Orchestrates frontend, backend, boundary, docs, and quality skills for normal feature work. |
| `frontend-app-dev` | Frontend app work with typed contracts, server-only secret handling, route handlers, rendering, and performance guardrails. |
| `backend-api-dev` | Backend API work with contract-first routing, schema/data changes, auth, service boundaries, and generation checks. |
| `backend-boundary-testing` | Focused seam tests for frontend-to-backend, auth, proxy, parser, and HTTP contract changes. |
| `branch-and-pr-discipline` | Branch, commit, push, and PR hygiene. |
| `codex-prompting-style` | High-signal prompts for coding agents and subprocess handoffs. |
| `dependency-reuse` | Reuse-first decisions before adding helpers, wrappers, packages, or scripts. |
| `docs-parity` | Keep canonical docs aligned with shipped behavior. |
| `is-it-good-enough` | Final adversarial quality gate before handoff. |
| `no-fallbacks` | Prevent silent fallbacks, compatibility layers, and permanent temporary paths. |
| `pragmatic-delivery` | Keep scope small, direct, and releasable. |
| `repo-boundaries` | Respect ownership boundaries in single-repo and multi-repo systems. |
| `testing-gates-and-harnesses` | Select verification gates based on touched risk. |

## Install Locally

Clone this repo once:

```bash
git clone git@github.com:ITECS-Dallas/agent-skills.git ~/Github/agent-skills
cd ~/Github/agent-skills
```

Validate the package:

```bash
node scripts/validate.mjs
```

Install skills for Codex and agent runtimes:

```bash
./scripts/install.sh --target both --mode symlink
```

Use `--mode copy` if the target runtime cannot follow symlinks. Use `--force` to replace existing installed skill folders with the same names.

## Attach To A Project

Agents generally do not read skills live from GitHub on every task. They read the skills that are available in their current local runtime, plugin cache, or repo-local instruction path. Treat this repo as the canonical source, then install or vendor it where the agent can actually load it.

Recommended model:

1. Keep this repo as the source of truth.
2. Install the skills globally on each workstation or agent host with `scripts/install.sh`.
3. In each project repo, add a short pointer in `AGENTS.md` or `CLAUDE.md` saying the shared skills come from this repo.
4. For strict reproducibility, pin this repo as a git submodule or subtree under the project and install from that pinned copy.
5. Update by pulling this repo, running validation, and reinstalling or refreshing symlinks.

For example, in an unrelated project:

```markdown
Shared agent skills source of truth: git@github.com:ITECS-Dallas/agent-skills.git
Install or refresh locally with:
  cd ~/Github/agent-skills
  git pull --ff-only
  node scripts/validate.mjs
  ./scripts/install.sh --target both --mode symlink --force
```

## Update Workflow

```bash
cd ~/Github/agent-skills
git pull --ff-only
node scripts/validate.mjs
./scripts/install.sh --target both --mode symlink --force
```

For project-pinned installs, update the submodule or subtree first, then rerun the install command from the pinned checkout.

## Rules For Contributors

- Keep skills project-neutral.
- Do not commit secrets, live `.env` files, tokens, client data, or private machine paths.
- Put project-specific rules in the target project's own docs.
- Keep `SKILL.md` frontmatter concise and trigger-focused.
- Prefer scripts for deterministic validation and repetitive installation steps.
- Run `node scripts/validate.mjs` before committing.
