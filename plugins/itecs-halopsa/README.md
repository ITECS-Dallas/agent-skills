# ITECS HaloPSA Plugin

`itecs-halopsa` packages the ITECS HaloPSA MCP connector for Codex. It provides the existing read tools plus guarded public-note, ticket-create, and ticket-status mutations.

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
- `halopsa.tickets.list`
- `halopsa.tickets.get`
- `halopsa.ticket_statuses.list`
- `halopsa.ticket_actions.list`
- `halopsa.ticket_actions.create_public_note`
- `halopsa.tickets.create`
- `halopsa.tickets.update_status`

Every write requires an exact preview and approval. Public notes retain their existing `confirm_public` gate. Ticket creation requires `APPROVE HALOPSA TICKET CREATE`. Status changes require `APPROVE HALOPSA STATUS CHANGE <ticket-id> TO <new-status-id>` and revalidate the current status immediately before the POST. Every mutation makes one attempt with no automatic retry; independently read back after every successful or ambiguous result.

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

The approved Brian Desmot setup uses `/opt/homebrew/bin/op-itecs read` command-backed values in `config.json` against Automation Vault item `GO-MCP HaloPSA Brian Desmot Read Write`. Resolve `HALO_CLIENT_ID`, `HALO_CLIENT_SECRET`, and `HALO_SCOPE` at runtime. Do not create secret-bearing `.env` files or fall back to plain `op`.

Each technician must use that technician's own `GO-MCP HaloPSA <Technician> Read Write` identity so HaloPSA attribution remains individual. The credential must retain the required read permissions and `edit:tickets`. Do not perform a live write test without one exact designated test record, complete preview, and required approval phrase.

Do not commit `.env`, local config JSON, API tokens, client secrets, raw HaloPSA exports, or generated billing reports.

### Windows Read/Write Identity

Each Windows technician's `~/.codex/halopsa-mcp/config.json` must use command-backed 1Password reads for that technician's exact `GO-MCP HaloPSA <Technician> Read Write` item:

```json
{
  "client_id_command": ["op", "--account", "<ITECS-account>", "read", "op://Automation Vault/GO-MCP HaloPSA <Technician> Read Write/HALO_CLIENT_ID"],
  "client_secret_command": ["op", "--account", "<ITECS-account>", "read", "op://Automation Vault/GO-MCP HaloPSA <Technician> Read Write/HALO_CLIENT_SECRET"],
  "scope_command": ["op", "--account", "<ITECS-account>", "read", "op://Automation Vault/GO-MCP HaloPSA <Technician> Read Write/HALO_SCOPE"]
}
```

These properties belong inside the configured server object alongside the existing base URL, token URL, timeout, retry, and page-size properties. Validate each `op read` with output redirected to null before restarting Codex. If the item is absent or inaccessible, stop for credential restoration or rotation; do not fall back to the shared identity or put a secret value in the config.

## Supported Platforms

Bundled MCP binaries are included for:

- macOS Apple Silicon: `darwin-arm64`
- macOS Intel: `darwin-amd64`
- Windows 11 x64: `windows-amd64.exe`
- Windows 11 ARM64: `windows-arm64.exe`

The plugin launcher is a Bash script. Windows 11 machines need Git Bash/MSYS/Cygwin Bash available as `bash` on `PATH`. WSL Bash is not supported for this launcher.

Windows preflight:

```powershell
where.exe bash
bash -lc 'case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) echo "Git Bash OK: $(uname -s)" ;; *) echo "Wrong bash for ITECS plugins: $(uname -s). Move Git Bash before WSL on PATH."; exit 1 ;; esac'
```

If startup fails with `/usr/bin/env: 'bash\r': No such file or directory`, refresh the plugin after the launcher line-ending fix and verify Git Bash is the active `bash`. That error happens before HaloPSA authentication and should not be treated as a vendor API permission issue.

## Install From The ITECS Marketplace

For another Codex installation:

```bash
codex plugin marketplace add git@github.com:ITECS-Dallas/agent-skills.git --ref main
codex plugin add itecs-halopsa@itecs-agent-skills
```

Start a new Codex thread after installing so the plugin MCP tools are loaded.

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
