# Agent Skills

Source-of-truth repository for ITECS reusable agent skills and Codex plugin packaging.

This repo serves two related purposes:

1. Maintain reusable engineering skills for Codex, Claude, and other local agent runtimes.
2. Publish the ITECS Codex plugin marketplace used to install grouped skills and MCP-backed business tools.

Most skills should remain project-neutral. ITECS-specific connector skills belong here only when they are intended to appear in the shared ITECS plugin surface. Project-specific rules, commands, secrets, approval gates, and deployment boundaries should stay in each project's `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, or equivalent local instruction file.

## Repository Contents

- `.agents/plugins/marketplace.json` - Codex marketplace definition named `itecs-agent-skills`.
- `plugins/portable-development-workflow/` - Codex plugin for reusable workflow skills and GO-MCP operating guidance.
- `plugins/portable-development-workflow/skills/` - skill source folders installed into local agent runtimes.
- `plugins/itecs-halopsa/` - Codex plugin that bundles the read-only HaloPSA MCP runtime and its HaloPSA skill.
- `plugins/itecs-vcenter/` - Codex plugin that bundles the read-only vCenter MCP runtime and its vCenter skill.
- `plugins/itecs-pax8/` - Codex plugin that bundles the read-only Pax8 MCP runtime and its Pax8 skill.
- `scripts/install.sh` - copies or symlinks portable skills into `$CODEX_HOME/skills` and `$AGENTS_HOME/skills`.
- `scripts/validate.mjs` - validates skill frontmatter, marketplace entries, plugin metadata, required files, and portability.
- `templates/project-skill-source-of-truth.md` - drop-in project docs for linking this repo from another project.

## Codex Plugins

| Install ID | Display Name | Purpose |
| --- | --- | --- |
| `portable-development-workflow@itecs-agent-skills` | ITECS Agent Skills | Reusable workflow and connector-operation skills for coding agents. |
| `itecs-halopsa@itecs-agent-skills` | ITECS HaloPSA | Bundled read-only HaloPSA MCP server exposing client, invoice, recurring-invoice, contract, purchase-order, project, ticket, ticket-action, and server-list lookup tools. |
| `itecs-vcenter@itecs-agent-skills` | ITECS vCenter | Bundled read-only vCenter MCP server for VM inventory, tags, hosting allocation, and billing evidence. |
| `itecs-pax8@itecs-agent-skills` | ITECS Pax8 | Bundled read-only Pax8 MCP server for companies, subscriptions, products, invoices, and billing evidence. |

The Codex plugin surface is repo-backed from this repository. It is not a global public marketplace publication path. Other Codex installations can install from the public GitHub URL or from an approved local clone.

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

## Install Skills Locally

Use this when you want the raw skills copied or symlinked into local agent skill directories. This is separate from installing the Codex plugins below.

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

## Attach Skills To A Project

Agents generally do not read skills live from GitHub on every task. They read the skills that are available in their current local runtime, plugin cache, or repo-local instruction path. Treat this repo as the canonical source, then install skills, install plugins, or vendor the repo where the agent can actually load it.

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

The skill install above exposes individual skill folders. The plugin install registers this repo as a Codex plugin marketplace so Codex can discover grouped plugins:

- `portable-development-workflow@itecs-agent-skills` for the reusable ITECS skill bundle.
- `itecs-halopsa@itecs-agent-skills` for live read-only HaloPSA MCP tools.
- `itecs-vcenter@itecs-agent-skills` for live read-only vCenter MCP tools.
- `itecs-pax8@itecs-agent-skills` for live read-only Pax8 MCP tools.

Add this repo as a local filesystem marketplace when the machine already has a clone:

```bash
codex plugin marketplace add ~/Github/agent-skills
```

Or add it from GitHub on another Codex installation:

```bash
codex plugin marketplace add git@github.com:ITECS-Dallas/agent-skills.git --ref main
```

Then install the skills plugin and any runtime connector plugins needed on that machine:

```bash
codex plugin add portable-development-workflow@itecs-agent-skills
codex plugin add itecs-halopsa@itecs-agent-skills
codex plugin add itecs-vcenter@itecs-agent-skills
codex plugin add itecs-pax8@itecs-agent-skills
```

Then restart Codex Desktop or start a new thread. Current threads do not automatically gain newly installed plugin MCP tools.

If Codex shows a plugin UI, enable or install:

- `ITECS Agent Skills` for the reusable skills bundle.
- `ITECS HaloPSA` for live HaloPSA MCP tools.
- `ITECS vCenter` for live vCenter MCP tools.
- `ITECS Pax8` for live Pax8 MCP tools.

If the plugin does not appear as enabled after adding the marketplace, confirm the marketplace was added and then add this block to the active Codex config file:

```toml
[plugins."portable-development-workflow@itecs-agent-skills"]
enabled = true

[plugins."itecs-halopsa@itecs-agent-skills"]
enabled = true

[plugins."itecs-vcenter@itecs-agent-skills"]
enabled = true

[plugins."itecs-pax8@itecs-agent-skills"]
enabled = true
```

Restart Codex Desktop after editing config.

### Windows 11 PowerShell Setup

Use this path on a Windows 11 workstation when the goal is to install the ITECS skills plugin and read-only GO-MCP connector plugins from the repo-backed marketplace without cloning the repo first.

Prerequisites:

- Codex Desktop or Codex CLI installed.
- Git for Windows installed, including Git Bash available as `bash` on `PATH`.
- Network access to `https://github.com/ITECS-Dallas/agent-skills`.
- GitHub authentication already working for Git, either through SSH or GitHub CLI.

Confirm Windows resolves `bash` to Git Bash, not WSL:

```powershell
where.exe bash
bash -lc 'case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) echo "Git Bash OK: $(uname -s)" ;; *) echo "Wrong bash for ITECS plugins: $(uname -s). Move Git Bash before WSL on PATH."; exit 1 ;; esac'
```

If the second command reports `Linux`, Codex is finding WSL Bash. Move the Git for Windows `bin` path ahead of WSL paths for the user account, then restart Codex Desktop and the terminal.

If using GitHub CLI for HTTPS authentication:

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
gh auth login
gh auth setup-git
```

Add the marketplace from PowerShell.

Use HTTPS if GitHub CLI is handling Git credentials:

```powershell
codex plugin marketplace add https://github.com/ITECS-Dallas/agent-skills.git --ref main
```

Or use SSH if the Windows machine has a working GitHub SSH key:

```powershell
codex plugin marketplace add git@github.com:ITECS-Dallas/agent-skills.git --ref main
```

Install the ITECS skills plugin and runtime connector plugins:

```powershell
codex plugin add portable-development-workflow@itecs-agent-skills
codex plugin add itecs-halopsa@itecs-agent-skills
codex plugin add itecs-vcenter@itecs-agent-skills
codex plugin add itecs-pax8@itecs-agent-skills
```

Confirm it is installed:

```powershell
codex plugin list
```

Then restart Codex Desktop or start a new thread. Current threads do not automatically gain newly installed plugin skills or MCP tools.

If the plugin does not appear as enabled, add this block to the active Codex config file, normally `%USERPROFILE%\.codex\config.toml`:

```toml
[plugins."portable-development-workflow@itecs-agent-skills"]
enabled = true

[plugins."itecs-halopsa@itecs-agent-skills"]
enabled = true

[plugins."itecs-vcenter@itecs-agent-skills"]
enabled = true

[plugins."itecs-pax8@itecs-agent-skills"]
enabled = true
```

Each runtime connector plugin launches through Bash and dispatches to the bundled macOS or Windows binary for the current machine.

To refresh from a local filesystem marketplace after this repo changes:

```bash
codex plugin add portable-development-workflow@itecs-agent-skills
codex plugin add itecs-halopsa@itecs-agent-skills
codex plugin add itecs-vcenter@itecs-agent-skills
codex plugin add itecs-pax8@itecs-agent-skills
```

For a Git-backed marketplace source, update the marketplace snapshot first, then reinstall the plugin entries:

```bash
codex plugin marketplace upgrade itecs-agent-skills
codex plugin add portable-development-workflow@itecs-agent-skills
codex plugin add itecs-halopsa@itecs-agent-skills
codex plugin add itecs-vcenter@itecs-agent-skills
codex plugin add itecs-pax8@itecs-agent-skills
```

To remove it:

```bash
codex plugin marketplace remove itecs-agent-skills
```

## GO-MCP Runtime Boundaries

The `itecs-halopsa`, `itecs-vcenter`, and `itecs-pax8` plugins package MCP launchers, bundled macOS and Windows binaries, and connector-specific skill instructions. Live credentials and runtime configuration stay outside this repo.

Current bundled binaries target:

- `darwin-arm64`
- `darwin-amd64`
- `windows-arm64.exe`
- `windows-amd64.exe`

Windows 11 machines require Git Bash/MSYS/Cygwin Bash available as `bash` on `PATH` because Codex starts each connector through its plugin launcher script. WSL Bash is not supported for these launchers.

Known Windows launcher failures:

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `bash` resolves to `Linux` or WSL | WSL Bash is ahead of Git Bash on `PATH` | Move Git for Windows Bash ahead of WSL paths, then restart Codex Desktop. |
| `/usr/bin/env: 'bash\r': No such file or directory` | Launcher was checked out with CRLF line endings or run through the wrong Bash runtime | Refresh this plugin after the `.gitattributes` line-ending fix and verify Git Bash is the active `bash`. |
| `codex.exe` under `WindowsApps` returns `Access is denied` | Windows app execution alias/shim is taking precedence over the user-local Codex binary | Use the Codex Desktop-supported binary path or correct the user `PATH`, then restart the terminal and Codex. |

Default local config paths:

```text
~/.codex/halopsa-mcp/config.json
~/.codex/vcenter-mcp/config.json
~/.codex/pax8-mcp/config.json
```

Optional per-session overrides:

```bash
export HALOPSA_MCP_CONFIG=/absolute/path/to/config.json
export VCENTER_MCP_CONFIG=/absolute/path/to/config.json
export PAX8_MCP_CONFIG=/absolute/path/to/config.json
```

Do not commit or paste connector `.env` files, config JSON, API tokens, client secrets, passwords, raw exports, generated billing reports, or customer data. GO-MCP workflows in this repo are read-only unless a task explicitly authorizes mutation.

Smoke-test installed plugin tool surfaces without printing secrets:

```bash
go run github.com/modelcontextprotocol/go-sdk/examples/client/listfeatures@latest \
  bash ~/Github/agent-skills/plugins/itecs-halopsa/scripts/run-halopsa-mcp
go run github.com/modelcontextprotocol/go-sdk/examples/client/listfeatures@latest \
  bash ~/Github/agent-skills/plugins/itecs-vcenter/scripts/run-vcenter-mcp
go run github.com/modelcontextprotocol/go-sdk/examples/client/listfeatures@latest \
  bash ~/Github/agent-skills/plugins/itecs-pax8/scripts/run-pax8-mcp
```

## Rules For Contributors

- Keep skills project-neutral.
- Do not commit secrets, live `.env` files, tokens, client data, or private machine paths.
- Put project-specific rules in the target project's own docs.
- Keep `SKILL.md` frontmatter concise and trigger-focused.
- Keep plugin manifests, marketplace entries, README install steps, and validation rules in sync.
- For MCP-backed plugins, keep credentials outside the plugin and document the read-only or write boundary clearly.
- Prefer scripts for deterministic validation and repetitive installation steps.
- Run `node scripts/validate.mjs` before committing.
