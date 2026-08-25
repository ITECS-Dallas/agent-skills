# ITECS HaloPSA Plugin

`itecs-halopsa` packages the ITECS HaloPSA MCP connector for Codex. It provides the existing read tools plus one guarded mutation that can add a public note to an exact ticket.

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
- `halopsa.ticket_actions.list`
- `halopsa.ticket_actions.create_public_note`

The public-note tool requires a positive ticket ID, a non-empty note, and `confirm_public: true`. It always uses public visibility, disables email, cannot change ticket status or other fields, and makes one POST attempt with no automatic retry. Independently read the ticket actions after every successful or ambiguous write.

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

The credential must retain the existing read permissions and include the ticket-edit permission required by `POST /Actions`. Do not perform a live write test without one exact designated HaloPSA test ticket and approval for the client-visible note.

Do not commit `.env`, local config JSON, API tokens, client secrets, raw HaloPSA exports, or generated billing reports.

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
