# ITECS HaloPSA Plugin

`itecs-halopsa` packages the ITECS read-only HaloPSA MCP connector for Codex. It is intended for finance, billing, purchase-order, and operations workflows that need live HaloPSA evidence without copying connector source code into each project.

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

## Runtime Configuration

Store live HaloPSA config and credentials outside this repository:

```text
~/.codex/halopsa-mcp/config.json
~/.codex/halopsa-mcp/.env
```

The launcher uses this config path by default:

```bash
~/.codex/halopsa-mcp/config.json
```

Override it per session with:

```bash
export HALOPSA_MCP_CONFIG=/absolute/path/to/config.json
```

Do not commit `.env`, local config JSON, API tokens, client secrets, raw HaloPSA exports, or generated billing reports.

## Install From The ITECS Marketplace

For another Codex installation with access to this private repo:

```bash
codex plugin marketplace add git@github.com:ITECS-Dallas/agent-skills.git --ref main
codex plugin add itecs-halopsa@itecs-agent-skills
```

Start a new Codex thread after installing so the plugin MCP tools are loaded.

## Local Smoke Test

From this plugin directory:

```bash
./scripts/run-halopsa-mcp -config ~/.codex/halopsa-mcp/config.json
```

For feature discovery without printing secrets:

```bash
go run github.com/modelcontextprotocol/go-sdk/examples/client/listfeatures \
  ./bin/halopsa-mcp-darwin-arm64 \
  -config ~/.codex/halopsa-mcp/config.json
```

Use `halopsa-mcp-darwin-amd64` on Intel macOS.

## Source Of Truth

The connector implementation source of truth remains the sibling GO-MCP checkout:

```text
GO-MCP/connectors/halopsa
```

Rebuild this plugin's binaries only from that connector after its tests pass.
