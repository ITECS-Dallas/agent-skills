# ITECS vCenter Plugin

`itecs-vcenter` packages the ITECS read-only vCenter MCP connector for Codex. It is intended for VM inventory, hosting allocation, client tag review, and billing evidence workflows.

## Tool Surface

The bundled MCP server exposes the current GO-MCP vCenter tools from `GO-MCP/connectors/vcenter`.

## Runtime Configuration

Store live vCenter config and credentials outside this repository:

```text
~/.codex/vcenter-mcp/config.json
~/.codex/vcenter-mcp/.env
```

The launcher uses this config path by default:

```bash
~/.codex/vcenter-mcp/config.json
```

Override it per session with:

```bash
export VCENTER_MCP_CONFIG=/absolute/path/to/config.json
```

Do not commit `.env`, local config JSON, passwords, tokens, raw vCenter exports, or generated billing reports.

## Supported Platforms

Bundled MCP binaries are included for:

- macOS Apple Silicon: `darwin-arm64`
- macOS Intel: `darwin-amd64`
- Windows 11 x64: `windows-amd64.exe`
- Windows 11 ARM64: `windows-arm64.exe`

The plugin launcher is a Bash script. Windows 11 machines need Git for Windows or another Bash runtime available as `bash` on `PATH`.

## Install From The ITECS Marketplace

For another Codex installation with access to this private repo:

```bash
codex plugin marketplace add git@github.com:ITECS-Dallas/agent-skills.git --ref main
codex plugin add itecs-vcenter@itecs-agent-skills
```

Start a new Codex thread after installing so the plugin MCP tools are loaded.

## Local Smoke Test

From this plugin directory:

```bash
bash ./scripts/run-vcenter-mcp
```

For feature discovery without printing secrets:

```bash
go run github.com/modelcontextprotocol/go-sdk/examples/client/listfeatures@latest \
  bash ./scripts/run-vcenter-mcp
```

## Source Of Truth

The connector implementation source of truth remains the sibling GO-MCP checkout:

```text
GO-MCP/connectors/vcenter
```

Rebuild this plugin's binaries only from that connector after its tests pass.
