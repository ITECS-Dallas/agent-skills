---
name: halopsa-mcp
description: Use when looking up live HaloPSA records or adding an explicitly approved public note to one exact HaloPSA ticket through the ITECS HaloPSA MCP plugin.
---

# HaloPSA MCP

## Purpose

Use the bundled HaloPSA MCP server for live lookup workflows and for one tightly governed write: adding a public/client-visible note to an exact ticket.

## Required Boundaries

- Keep all activity read-only unless the user explicitly requests a public note on one exact ticket and approves the exact client-visible text.
- Before a public note, re-read the exact ticket, verify its client and context, preview the complete note, identify it as public/client-visible, and obtain the workflow's exact approval phrase.
- Use only `halopsa.ticket_actions.create_public_note` with the approved ticket ID and note body and `confirm_public: true`. Never substitute a direct HTTP request or browser write.
- After a successful or ambiguous call, use `halopsa.ticket_actions.list` for independent read-back. Never automatically retry an ambiguous write.
- The public-note tool cannot email, change status, log time, attach files, or create private notes. Treat every other HaloPSA mutation as out of scope.
- Do not print or commit HaloPSA credentials, local config JSON, OAuth tokens, client secrets, raw exports, generated billing reports, or sensitive customer detail unless the user explicitly asks for the detail.
- Use local runtime config under `~/.codex/halopsa-mcp/`.
- Standard technician setup uses 1Password CLI command-backed secrets from item `GO-MCP HaloPSA Read Only`; do not create or depend on local secret-bearing `.env` files.
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
- `halopsa.projects.list` - list projects with client, site, agent, status, milestone, team, text, date, and pagination filters.
- `halopsa.projects.get` - get one project by ID.
- `halopsa.tickets.list` - list tickets with client, site, user, agent, status, priority, team, text, date, and pagination filters.
- `halopsa.tickets.get` - get one ticket by ID, optionally including recent actions/notes.
- `halopsa.ticket_actions.list` - list ticket actions/notes for a specific ticket.
- `halopsa.ticket_actions.create_public_note` - add one public/client-visible note to an exact ticket after explicit approval; no email, status, time, attachment, or private-note side effects.

## Operating Pattern

1. Confirm the user's goal and the minimum HaloPSA data needed.
2. Use narrow filters before broad list calls.
3. For purchase-order review, start with `halopsa.purchase_orders.list`, then call `halopsa.purchase_orders.get` only for candidate matches that need line-level evidence.
4. For service desk or project review, start with the narrowest relevant `halopsa.tickets.list` or `halopsa.projects.list` filters, then call the corresponding `get` tool only for records that need detail.
5. Preserve evidence fields in the answer: HaloPSA ID, reference, supplier/client, dates, status, total, and match rationale.
6. Report uncertainty plainly when a lookup is inconclusive.
7. For a requested public note, verify the exact ticket, preview and approve the exact note, write once, then independently read back the action before claiming publication.

## Local Setup

Each machine needs local config outside the plugin:

```text
~/.codex/halopsa-mcp/config.json
```

The Brian Desmot configuration must call `/opt/homebrew/bin/op-itecs read` for these approved Automation Vault item fields:

```text
op://Automation Vault/GO-MCP HaloPSA Brian Desmot Read Write/HALO_CLIENT_ID
op://Automation Vault/GO-MCP HaloPSA Brian Desmot Read Write/HALO_CLIENT_SECRET
op://Automation Vault/GO-MCP HaloPSA Brian Desmot Read Write/HALO_SCOPE
```

The plugin launcher also honors:

```bash
HALOPSA_MCP_CONFIG=/absolute/path/to/config.json
```

Never store credentials in this plugin repository.

## Windows Startup Troubleshooting

If HaloPSA tools are not callable, check startup layers before checking vendor auth:

1. Confirm the plugin is installed and the Codex thread was started after install.
2. On Windows, confirm `bash -lc 'uname -s'` returns `MINGW`, `MSYS`, or `CYGWIN`; WSL Bash is not supported.
3. Treat `/usr/bin/env: 'bash\r': No such file or directory` as a launcher line-ending or wrong-Bash-runtime issue, not a HaloPSA API issue.
4. Treat `codex.exe` under `WindowsApps` returning `Access is denied` as a local Codex/PATH issue.
5. On the ITECS Mac, confirm `/opt/homebrew/bin/op-itecs` can read the configured fields without printing their values. Stop on failure; do not fall back to plain `op`.
