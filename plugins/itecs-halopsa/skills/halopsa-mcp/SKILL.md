---
name: halopsa-mcp
description: Use when looking up live HaloPSA clients, invoices, recurring invoices, contracts, purchase orders, or server configuration through the ITECS read-only HaloPSA MCP plugin.
---

# HaloPSA MCP

## Purpose

Use the bundled read-only HaloPSA MCP server for live HaloPSA lookup workflows in Codex. This plugin is appropriate for CFOAGENT purchase-order review, billing evidence, client lookup, invoice lookup, recurring-invoice review, contract lookup, and connector availability checks.

## Required Boundaries

- Keep all HaloPSA actions read-only.
- Do not print or commit HaloPSA credentials, `.env` contents, local config JSON, OAuth tokens, client secrets, raw exports, generated billing reports, or sensitive customer detail unless the user explicitly asks for the detail.
- Use local runtime config under `~/.codex/halopsa-mcp/`.
- Keep MCP stdout reserved for protocol traffic.
- Summarize results by default; provide row-level details only when the user requests them.

## Available Tools

- `halopsa.servers.list` - list configured HaloPSA targets without exposing credentials.
- `halopsa.clients.list` - list clients with search, active/inactive, and pagination filters.
- `halopsa.clients.get` - get one client by ID.
- `halopsa.invoices.list` - list invoices with client, date, payment, sent, and pagination filters.
- `halopsa.invoices.get` - get one invoice by ID.
- `halopsa.recurring_invoices.list` - list recurring invoices with client, date, sent, ready-for-invoicing, and pagination filters.
- `halopsa.recurring_invoices.get` - get one recurring invoice by ID.
- `halopsa.contracts.list` - list client contracts with client, site, type, renewal, and pagination filters.
- `halopsa.contracts.get` - get one client contract by ID.
- `halopsa.purchase_orders.list` - list purchase orders with open/closed status, supplier, client, ticket, search, and pagination filters.
- `halopsa.purchase_orders.get` - get one purchase order by ID.

## Operating Pattern

1. Confirm the user's goal and the minimum HaloPSA data needed.
2. Use narrow filters before broad list calls.
3. For purchase-order review, start with `halopsa.purchase_orders.list`, then call `halopsa.purchase_orders.get` only for candidate matches that need line-level evidence.
4. Preserve evidence fields in the answer: HaloPSA ID, reference, supplier/client, dates, status, total, and match rationale.
5. Report uncertainty plainly when a lookup is inconclusive.

## Local Setup

Each machine needs local config outside the plugin:

```text
~/.codex/halopsa-mcp/config.json
~/.codex/halopsa-mcp/.env
```

The plugin launcher also honors:

```bash
HALOPSA_MCP_CONFIG=/absolute/path/to/config.json
```

Never store credentials in this plugin repository.
