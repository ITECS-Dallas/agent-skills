# ITECS HaloPSA for Atlas

Version 0.11.0 packages the existing 34 typed tools (21 reads and 13 writes) for macOS, Windows and Linux, including tenant metadata and the authenticated technician. Routine internal requests use existing chat authorization. Client-visible and billing changes use a single ordinary confirmation. All writes use `confirm`; no exact approval phrases are required.

See [the runtime workflow](skills/halopsa-mcp/SKILL.md) for current operation behavior and [Linux support-agent setup](docs/linux-support-agent.md) for ChatGPT subscription authentication, packaging and the canonical `/home/itecs/US1/ATLAS` documentation workspace. The optional [client troubleshooting skill](skills/service-desk-client-troubleshooting/SKILL.md) continues replies on an existing ticket and closes only after the client clearly confirms resolution. Restart into a new Codex task after updating the plugin.

## Tool Surface

The bundled MCP server exposes the current GO-MCP HaloPSA tools:

- `halopsa.servers.list`
- `halopsa.metadata.list`
- `halopsa.agents.me`
- `halopsa.clients.list`
- `halopsa.clients.get`
- `halopsa.invoices.list`
- `halopsa.invoices.get`
- `halopsa.recurring_invoices.list`
- `halopsa.recurring_invoices.get`
- `halopsa.contracts.list`
- `halopsa.contracts.get`
- `halopsa.contracts.create`
- `halopsa.contracts.update`
- `halopsa.purchase_orders.list`
- `halopsa.purchase_orders.get`
- `halopsa.projects.list`
- `halopsa.projects.get`
- `halopsa.projects.create`
- `halopsa.projects.update`
- `halopsa.projects.update_status`
- `halopsa.tickets.list`
- `halopsa.tickets.get`
- `halopsa.ticket_statuses.list`
- `halopsa.ticket_actions.list`
- `halopsa.ticket_outcomes.list`
- `halopsa.ticket_outcomes.get`
- `halopsa.ticket_actions.start_work`
- `halopsa.ticket_actions.send_email`
- `halopsa.ticket_actions.create_public_note`
- `halopsa.ticket_actions.create_private_note`
- `halopsa.ticket_actions.create_time_entry`
- `halopsa.tickets.create`
- `halopsa.tickets.update`
- `halopsa.tickets.update_status`

Ticket action reads support conversation/public filters, date windows and optional email HTML. Keep `agent_only` false to include client replies, and preserve action IDs/authorship when continuing a conversation.

Technicians can request a ticket or project in ordinary chat. The agent resolves supplied names to HaloPSA IDs and asks concise follow-up questions only when required values remain missing; technicians do not compose tool payloads. Ticket and project creation require at least one category ID plus positive HaloPSA impact and urgency values.

All write tools use `confirm`: omitted or false for preview, true for execution. An explicit technician request authorizes routine internal notes, specified time, assignment/field updates and Start Work. Review client-visible, creation/status and billing changes with one ordinary confirmation. Snapshot/status revalidation and independent readback remain part of execution; ambiguous writes are not automatically retried.

When a technician authorizes the optional client troubleshooting conversation, that authorization covers its invitation, relevant replies, progress notes and closure after the client's clear resolution confirmation. Do not request repeated technician confirmation for those actions. A failed diagnostic can lead to the next applicable documented step. Decline, a request for a technician, exhausted procedures/capabilities or an unresolved issue requiring escalation lead to a handoff; unresolved issues and no response leave the ticket open. This is an on-demand Codex workflow using the existing tools; it does not install a background agent or poller.

`Start Work` resolves exactly one currently available tenant outcome named `Start Work` and posts that outcome through `/Actions`; it never substitutes a generic status update. Outcome metadata can disclose configured status, assignment, workflow, email, billing, and timer effects. Halo's continuously running browser timer is UI state, so the connector does not claim that it remains open. Explicit time logging is supported through `halopsa.ticket_actions.create_time_entry`.

Ticket email uses one exact email-capable configured outcome and `confirm: true` for the authorized execution. It does not write directly to Halo's outgoing-email queue.

## Runtime Configuration

Store live HaloPSA config and credentials outside this repository:

```text
~/.codex/halopsa-mcp/config.json
```

The launcher uses this config path by default:

```bash
~/.codex/halopsa-mcp/config.json
```

Override it per session with:

```bash
export HALOPSA_MCP_CONFIG=/absolute/path/to/config.json
```

Each technician uses that technician's own Automation Vault item named `GO-MCP HaloPSA <Technician> Read Write`. The setup scripts validate all six expected fields, exact agent identity, approved URLs, least-privilege ticket scopes, and OAuth before writing a config. The generated file contains only command-backed references for `HALO_CLIENT_ID`, `HALO_CLIENT_SECRET`, and `HALO_SCOPE`; it never contains resolved credentials.

Each technician must use that technician's own `GO-MCP HaloPSA <Technician> Read Write` identity so HaloPSA attribution remains individual. The credential must retain the required read permissions and `edit:tickets`. A live write test uses the technician's designated test record and authorized action with the existing preview and readback behavior.

Do not commit `.env`, local config JSON, API tokens, client secrets, raw HaloPSA exports, or generated billing reports.

### macOS Setup

Use the managed prompt-free ITECS wrapper. Do not fall back to plain `op`:

```bash
./scripts/configure-halopsa-mcp-macos.sh --technician "Exact Technician Name"
```

Use `--force` only when intentionally replacing that technician's existing local config.

### Linux Setup

Run from the installed plugin directory as the Linux account that runs Codex:

```bash
./scripts/configure-halopsa-mcp-linux.sh --technician "Exact Technician Name"
```

The script resolves the managed prompt-free `op-itecs` wrapper on `PATH`. Use `--op-command /absolute/path/to/op-itecs` when it is installed elsewhere. It shares the existing Automation Vault, identity, scope and OAuth validation with macOS, and writes command references to `~/.codex/halopsa-mcp/config.json`. See [the Linux guide](docs/linux-support-agent.md) for prerequisites, installation and Codex login.

### Windows 11 Setup

Run in PowerShell from the installed plugin directory:

```powershell
.\scripts\configure-halopsa-mcp-windows.ps1 `
  -TechnicianName "Exact Technician Name" `
  -ItecsAccount "ITECS-1PASSWORD-ACCOUNT-SHORTHAND"
```

The Windows script resolves the installed `op.exe`, validates the exact per-technician Automation Vault item and live OAuth response, and writes `%USERPROFILE%\.codex\halopsa-mcp\config.json` with command references only. If the item is absent, inaccessible, mismatched, over-scoped, or rejected by OAuth, stop for credential restoration/rotation; do not use another technician's identity or a shared fallback.

## Supported Platforms

Bundled MCP binaries are included for:

- macOS Apple Silicon: `darwin-arm64`
- macOS Intel: `darwin-amd64`
- Linux x64: `linux-amd64`
- Linux ARM64: `linux-arm64`
- Windows 11 x64: `windows-amd64.exe`
- Windows 11 ARM64: `windows-arm64.exe`

The plugin launcher is a Bash script. Windows 11 machines need Git Bash/MSYS/Cygwin Bash available as `bash` on `PATH`; it resolves the default config from `%USERPROFILE%` so PowerShell setup and Git Bash startup use the same file. WSL Bash is not supported for this launcher.

Windows preflight:

```powershell
where.exe bash
bash -lc 'case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) echo "Git Bash OK: $(uname -s)" ;; *) echo "Wrong bash for ITECS plugins: $(uname -s). Move Git Bash before WSL on PATH."; exit 1 ;; esac'
```

If startup fails with `/usr/bin/env: 'bash\r': No such file or directory`, refresh the plugin after the launcher line-ending fix and verify Git Bash is the active `bash`. That error happens before HaloPSA authentication and should not be treated as a vendor API permission issue.

## Install From The ITECS Marketplace

For another Codex installation:

```bash
codex plugin marketplace add https://github.com/ITECS-Dallas/agent-skills.git --ref main
codex plugin add itecs-halopsa@itecs-agent-skills
```

Start a new Codex thread after installing so the plugin MCP tools are loaded.

## Refresh An Existing Installation

After this marketplace repository is updated, reinstall the plugin so Codex refreshes its cached runtime:

```bash
codex plugin add itecs-halopsa@itecs-agent-skills
```

Then restart Codex Desktop or start a new thread. Existing threads keep the tool schema that was loaded when the thread started.

## Local Smoke Test

From this plugin directory:

```bash
bash ./scripts/run-halopsa-mcp
```

For feature discovery without printing secrets:

```bash
go run github.com/modelcontextprotocol/go-sdk/examples/client/listfeatures@latest \
  bash ./scripts/run-halopsa-mcp
```

## Source Of Truth

The connector implementation source of truth remains the sibling GO-MCP checkout:

```text
GO-MCP/connectors/halopsa
```

Rebuild this plugin's binaries only from that connector after its tests pass.

## Packaged reporting and diagnostics

ITECS Billing Audit provides source Excel/JSON reports and the staged reconciliation commands without Go or a developer checkout. Use its `scripts/run-source-report halopsa -month YYYY-MM -json-only=false -out-dir /absolute/output/path`. Ordinary lookups continue to use this plugin's bundled MCP tools.

Run `scripts/doctor` for optional local version, platform and config-presence diagnostics (Python 3). Add `--discover` to list the actual MCP tools; discovery starts the configured server and resolves its credential commands but invokes no vendor operation. Config contents and credential values are not printed. `BUILD-MANIFEST.json` records the source revision, platform binaries and SHA-256 hashes.
