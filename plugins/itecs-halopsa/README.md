# ITECS HaloPSA Plugin

`itecs-halopsa` packages the ITECS HaloPSA MCP connector for Codex. It provides read tools plus approval-gated ticket and project operations. Internal/private notes are the default. Public notes require an explicit client-visible request. No tool exposes email, reply-to-user, arbitrary action, attachment, deletion, or raw API passthrough.

## Tool Surface

The bundled MCP server exposes the current GO-MCP HaloPSA tools:

- `halopsa.servers.list`
- `halopsa.clients.list`
- `halopsa.clients.get`
- `halopsa.invoices.list`
- `halopsa.invoices.get`
- `halopsa.recurring_invoices.list`
- `halopsa.recurring_invoices.get`
- `halopsa.contracts.list`
- `halopsa.contracts.get`
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
- `halopsa.ticket_actions.create_public_note`
- `halopsa.ticket_actions.create_private_note`
- `halopsa.ticket_actions.create_time_entry`
- `halopsa.tickets.create`
- `halopsa.tickets.update`
- `halopsa.tickets.update_status`

Technicians can request a ticket or project in ordinary chat. The agent resolves supplied names to HaloPSA IDs and asks concise follow-up questions only when required values remain missing; technicians do not compose tool payloads. Ticket and project creation require at least one category ID plus positive HaloPSA impact and urgency values.

Every write requires one exact preview and the connector-required confirmation. Omit `approval_phrase` from `halopsa.tickets.create` to preview, then use the returned `APPROVE HALOPSA TICKET CREATE` phrase once. Omit `confirm` from `halopsa.projects.create` to preview, then use one plain confirmation passed as `confirm: true`. Private notes use `APPROVE HALOPSA PRIVATE NOTE <ticket-id>`; time entries use `APPROVE HALOPSA TIME ENTRY <ticket-id>` and are always private/non-email. Public notes retain their explicit `confirm_public` gate. Field updates require an immediately read `last_update`; status updates revalidate the current and allowed target statuses. Every mutation makes one POST attempt with no automatic retry; independently read back after every successful or ambiguous result.

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

Each technician must use that technician's own `GO-MCP HaloPSA <Technician> Read Write` identity so HaloPSA attribution remains individual. The credential must retain the required read permissions and `edit:tickets`. Do not perform a live write test without one exact designated test record, complete preview, and required approval phrase.

Do not commit `.env`, local config JSON, API tokens, client secrets, raw HaloPSA exports, or generated billing reports.

### macOS Setup

Use the managed prompt-free ITECS wrapper. Do not fall back to plain `op`:

```bash
./scripts/configure-halopsa-mcp-macos.sh --technician "Exact Technician Name"
```

Use `--force` only when intentionally replacing that technician's existing local config.

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
