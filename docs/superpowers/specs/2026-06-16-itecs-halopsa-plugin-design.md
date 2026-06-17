# ITECS HaloPSA Plugin Design

Date: June 16, 2026
Status: Approved by Brian Desmot

## Goal

Package the existing GO-MCP HaloPSA connector as a real Codex marketplace plugin named `itecs-halopsa` inside the existing `ITECS-Dallas/agent-skills` marketplace.

## Scope

The plugin must expose the full current HaloPSA MCP tool surface, not only purchase-order lookups:

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

## Architecture

`GO-MCP/connectors/halopsa` remains the source of truth for connector implementation. `agent-skills/plugins/itecs-halopsa` bundles compiled Mac binaries plus Codex plugin metadata, MCP server config, a launcher script, and a HaloPSA operating skill. The launcher reads local config from `HALOPSA_MCP_CONFIG` or `~/.codex/halopsa-mcp/config.json`; credentials remain outside Git.

## Safety

The plugin is read-only. It must not store credentials, `.env` files, tokens, local config, raw HaloPSA outputs, or generated billing reports. Runtime configuration stays under `~/.codex/halopsa-mcp/` on each machine.

## Validation

Validation must prove:

- The agent-skills marketplace registers `itecs-halopsa`.
- The plugin manifest declares skills and MCP servers.
- The plugin wrapper and binaries are executable.
- The GO-MCP HaloPSA connector tests pass.
- The compiled plugin binary advertises all expected MCP tools through the SDK `listfeatures` smoke test.
