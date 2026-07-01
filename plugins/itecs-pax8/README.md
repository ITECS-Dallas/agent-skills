# ITECS Pax8 Plugin

`itecs-pax8` packages the ITECS read-only Pax8 MCP connector for Codex. It is intended for company, subscription, product, invoice, draft invoice item, billing evidence, and Pax8-to-HaloPSA reconciliation workflows.

## Tool Surface

The bundled MCP server exposes the current GO-MCP Pax8 tools from `GO-MCP/connectors/pax8`.

## Runtime Configuration

Store live Pax8 config and credentials outside this repository:

```text
~/.codex/pax8-mcp/config.json
```

The launcher uses this config path by default:

```bash
~/.codex/pax8-mcp/config.json
```

Override it per session with:

```bash
export PAX8_MCP_CONFIG=/absolute/path/to/config.json
```

The standard ITECS setup uses `op read` command-backed secrets in `config.json` against the `GO-MCP Pax8 Read Only` 1Password item. Do not create secret-bearing `.env` files for the standard technician workflow.

Do not commit `.env`, local config JSON, API tokens, client secrets, raw Pax8 exports, or generated billing reports.

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

If startup fails with `/usr/bin/env: 'bash\r': No such file or directory`, refresh the plugin after the launcher line-ending fix and verify Git Bash is the active `bash`. That error happens before Pax8 authentication and should not be treated as a vendor API permission issue.

## Install From The ITECS Marketplace

For another Codex installation:

```bash
codex plugin marketplace add git@github.com:ITECS-Dallas/agent-skills.git --ref main
codex plugin add itecs-pax8@itecs-agent-skills
```

Start a new Codex thread after installing so the plugin MCP tools are loaded.

## Local Smoke Test

From this plugin directory:

```bash
bash ./scripts/run-pax8-mcp
```

For feature discovery without printing secrets:

```bash
go run github.com/modelcontextprotocol/go-sdk/examples/client/listfeatures@latest \
  bash ./scripts/run-pax8-mcp
```

## Source Of Truth

The connector implementation source of truth remains the sibling GO-MCP checkout:

```text
GO-MCP/connectors/pax8
```

Rebuild this plugin's binaries only from that connector after its tests pass.
