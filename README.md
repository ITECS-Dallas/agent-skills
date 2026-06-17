# Agent Skills

ITECS agent skills for Codex, Claude, and other coding agents.

This repo is the source of truth for reusable agent guidance. Most skills are project-neutral. ITECS-specific connector skills are included here when they should appear in the ITECS Agent Skills plugin rather than only as repo-local runbooks. Project-specific rules should stay in each project's `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, or equivalent local instruction file.

## What Is Included

- `plugins/portable-development-workflow/` - Codex plugin-ready bundle for the ITECS Agent Skills marketplace.
- `plugins/portable-development-workflow/skills/` - reusable workflow skills plus ITECS GO-MCP connector skills.
- `plugins/itecs-halopsa/` - Codex plugin that bundles the read-only HaloPSA MCP runtime.
- `scripts/install.sh` - copies or symlinks skills into local agent skill directories.
- `scripts/validate.mjs` - validates skill frontmatter, plugin metadata, and portability.
- `templates/project-skill-source-of-truth.md` - drop-in project docs for linking this repo from another project.

## Codex Plugins

| Plugin | Purpose |
| --- | --- |
| `portable-development-workflow` | Reusable workflow and connector-operation skills for coding agents. |
| `itecs-halopsa` | Bundled read-only HaloPSA MCP server exposing client, invoice, recurring-invoice, contract, purchase-order, and server-list lookup tools. |

## Skill Catalog

| Skill | Use |
| --- | --- |
| `project-development-workflow` | Orchestrates frontend, backend, boundary, docs, and quality skills for normal feature work. |
| `seo-audit` | Audits and improves technical SEO, metadata, schema, local search, content, public crawlability, and AI visibility. |
| `frontend-app-dev` | Frontend app work with typed contracts, server-only secret handling, route handlers, rendering, and performance guardrails. |
| `grill-me` | Decision-tree interview flow for ambiguous plans, remediation paths, workflow changes, and implementation scope. |
| `halopsa-mcp` | Operate the GO-MCP HaloPSA read-only billing connector and recurring-invoice audit workflow. |
| `backend-api-dev` | Backend API work with contract-first routing, schema/data changes, auth, service boundaries, and generation checks. |
| `backend-boundary-testing` | Focused seam tests for frontend-to-backend, auth, proxy, parser, and HTTP contract changes. |
| `branch-and-pr-discipline` | Branch, commit, push, and PR hygiene. |
| `codex-prompting-style` | High-signal prompts for coding agents and subprocess handoffs. |
| `dependency-reuse` | Reuse-first decisions before adding helpers, wrappers, packages, or scripts. |
| `docs-parity` | Keep canonical docs aligned with shipped behavior. |
| `is-it-good-enough` | Final adversarial quality gate before handoff. |
| `no-fallbacks` | Prevent silent fallbacks, compatibility layers, and permanent temporary paths. |
| `pax8-mcp` | Operate the GO-MCP Pax8 read-only billing source connector and Pax8-to-HaloPSA audit workflow. |
| `pragmatic-delivery` | Keep scope small, direct, and releasable. |
| `repo-boundaries` | Respect ownership boundaries in single-repo and multi-repo systems. |
| `testing-gates-and-harnesses` | Select verification gates based on touched risk. |
| `vcenter-mcp` | Operate the GO-MCP vCenter read-only inventory and billable VM audit workflow. |

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

## New Project Setup

Use this flow after the new project already has a GitHub repo and a local checkout.

1. Clone or enter the project repo.

```bash
cd ~/Github
git clone git@github.com:ORG/NEW-REPO.git
cd NEW-REPO
```

2. Refresh the shared skills source repo.

```bash
cd ~/Github/agent-skills
git pull --ff-only
node scripts/validate.mjs
```

3. Install or refresh the shared skills locally.

```bash
./scripts/install.sh --target both --mode symlink --force
```

Use `--mode copy` instead of `--mode symlink` only when the target runtime or host cannot follow symlinks.

4. Add a project-local pointer file. For Codex, prefer `AGENTS.md`; for Claude, prefer `CLAUDE.md`. It is fine to keep both if the project uses both tools.

```md
# Shared Agent Skills

Shared agent skills source of truth:
git@github.com:ITECS-Dallas/agent-skills.git

Use the globally installed shared skills for reusable engineering workflow.
Project-local instructions in this file override shared skills when they conflict.

Project-specific rules belong here:
- repo roots and app boundaries
- local commands
- deployment boundaries
- environment names
- approval gates
- testing requirements
```

5. Commit the project-local pointer.

```bash
git add AGENTS.md
git commit -m "docs: add shared agent skills guidance"
git push
```

6. Start a new Codex or Claude session in the project checkout.

New sessions should pick up the globally installed skills. If the app was already open, restart the app or start a new thread so the skill registry refreshes.

## Pinned Per-Project Setup

Use this mode when a project must pin an exact version of the shared skills instead of always tracking the workstation-global checkout.

```bash
cd ~/Github/NEW-REPO
git submodule add git@github.com:ITECS-Dallas/agent-skills.git .agents/vendor/agent-skills
git commit -m "chore: pin shared agent skills"
```

Install from the pinned copy:

```bash
cd .agents/vendor/agent-skills
node scripts/validate.mjs
./scripts/install.sh --target both --mode symlink --force
```

Update a pinned project later:

```bash
cd ~/Github/NEW-REPO/.agents/vendor/agent-skills
git pull --ff-only
node scripts/validate.mjs
cd ~/Github/NEW-REPO
git add .agents/vendor/agent-skills
git commit -m "chore: update shared agent skills"
git push
```

## Install As Codex Plugins

The symlink install above makes the individual skills available. The plugin install registers this repo as a Codex plugin marketplace so Codex can discover the grouped `portable-development-workflow` plugin and the runtime `itecs-halopsa` MCP plugin.

Add this repo as a local marketplace:

```bash
codex plugin marketplace add ~/Github/agent-skills
```

Or add it from GitHub:

```bash
codex plugin marketplace add git@github.com:ITECS-Dallas/agent-skills.git --ref main
```

Then install one or both plugins:

```bash
codex plugin add portable-development-workflow@itecs-agent-skills
codex plugin add itecs-halopsa@itecs-agent-skills
```

Then restart Codex Desktop or start a new thread. If Codex shows a plugin UI, enable or install `ITECS Agent Skills` for the skills bundle and `ITECS HaloPSA` for live HaloPSA MCP tools.

If the plugin does not appear as enabled after adding the marketplace, confirm the marketplace was added and then add this block to the active Codex config file:

```toml
[plugins."portable-development-workflow@itecs-agent-skills"]
enabled = true

[plugins."itecs-halopsa@itecs-agent-skills"]
enabled = true
```

Restart Codex Desktop after editing config.

To refresh a local marketplace install after this repo changes:

```bash
codex plugin add portable-development-workflow@itecs-agent-skills
codex plugin add itecs-halopsa@itecs-agent-skills
```

For a Git-backed marketplace source, upgrade the marketplace snapshot first:

```bash
codex plugin marketplace upgrade itecs-agent-skills
```

To remove it:

```bash
codex plugin marketplace remove itecs-agent-skills
```

## Rules For Contributors

- Keep skills project-neutral.
- Do not commit secrets, live `.env` files, tokens, client data, or private machine paths.
- Put project-specific rules in the target project's own docs.
- Keep `SKILL.md` frontmatter concise and trigger-focused.
- Prefer scripts for deterministic validation and repetitive installation steps.
- Run `node scripts/validate.mjs` before committing.
