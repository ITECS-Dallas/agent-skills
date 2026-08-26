---
name: halopsa-mcp
description: Use when looking up live HaloPSA records or performing an explicitly approved public note, ticket creation, or status change through the ITECS HaloPSA MCP plugin.
---

# HaloPSA MCP

## Purpose

Use the bundled HaloPSA MCP server for live lookup workflows and for tightly governed writes to one exact ticket at a time.

## Required Boundaries

- Keep all activity read-only unless the user explicitly requests one exact supported mutation and approves its complete preview.
- Before a public note, re-read the exact ticket, verify its client and context, preview the complete note, identify it as public/client-visible, and obtain the workflow's exact approval phrase.
- Use only `halopsa.ticket_actions.create_public_note` with the approved ticket ID and note body and `confirm_public: true`. Never substitute a direct HTTP request or browser write.
- Before ticket creation, verify the exact client, site/user when supplied, ticket type, priority/team/agent when supplied, summary, and details. Warn that tenant rules or workflows may still send notifications. Preview every field and obtain the exact phrase `APPROVE HALOPSA TICKET CREATE`; then call `halopsa.tickets.create` once.
- Before a status change or resolution, read the exact ticket and `halopsa.ticket_statuses.list`, preview the current and target status IDs and names, warn that tenant rules or workflows may activate, and obtain `APPROVE HALOPSA STATUS CHANGE <ticket-id> TO <new-status-id>`. Pass the immediately read current status as `expected_current_status_id` and call `halopsa.tickets.update_status` once.
- After a successful or ambiguous call, independently read back the ticket or actions. Never automatically retry an ambiguous write.
- The public-note tool cannot email, change status, log time, attach files, or create private notes. The ticket-create and status tools cannot add time, attachments, private notes, or arbitrary ticket fields. Treat every other HaloPSA mutation as out of scope.
- Do not print or commit HaloPSA credentials, local config JSON, OAuth tokens, client secrets, raw exports, generated billing reports, or sensitive customer detail unless the user explicitly asks for the detail.
- Use local runtime config under `~/.codex/halopsa-mcp/`.
- Standard technician setup uses 1Password CLI command-backed secrets from the technician's approved `GO-MCP HaloPSA <Technician> Read Write` item. Do not use a shared API identity or create local secret-bearing `.env` files.
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
- `halopsa.ticket_statuses.list` - list ticket statuses, optionally narrowed to an exact ticket or ticket type.
- `halopsa.ticket_actions.list` - list ticket actions/notes for a specific ticket.
- `halopsa.ticket_actions.create_public_note` - add one public/client-visible note to an exact ticket after explicit approval; no email, status, time, attachment, or private-note side effects.
- `halopsa.tickets.create` - create one approved ticket with explicit routing and content fields; one attempt only.
- `halopsa.tickets.update_status` - change one exact ticket's status only after current-status revalidation and exact approval; one attempt only.

## Operating Pattern

1. Confirm the user's goal and the minimum HaloPSA data needed.
2. Use narrow filters before broad list calls.
3. For purchase-order review, start with `halopsa.purchase_orders.list`, then call `halopsa.purchase_orders.get` only for candidate matches that need line-level evidence.
4. For service desk or project review, start with the narrowest relevant `halopsa.tickets.list` or `halopsa.projects.list` filters, then call the corresponding `get` tool only for records that need detail.
5. Preserve evidence fields in the answer: HaloPSA ID, reference, supplier/client, dates, status, total, and match rationale.
6. Report uncertainty plainly when a lookup is inconclusive.
7. For any supported write, verify the exact target and context, preview every changed field and possible visibility/notification effect, obtain the required exact approval phrase, write once, and independently read back before claiming completion.

## Local Setup

Each machine needs local config outside the plugin:

```text
~/.codex/halopsa-mcp/config.json
```

The Brian Desmot configuration on the managed Mac must call `/opt/homebrew/bin/op-itecs read` for these approved Automation Vault item fields:

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

On Windows 11 technician workstations, use the installed 1Password CLI with command-backed reads to that technician's approved read/write item. Do not copy a credential value into `config.json`; do not use another technician's item. If the named item is absent or inaccessible, stop and have an authorized credential operator restore or rotate that technician's credential rather than falling back to the shared read-only identity.

## Windows Startup Troubleshooting

If HaloPSA tools are not callable, check startup layers before checking vendor auth:

1. Confirm the plugin is installed and the Codex thread was started after install.
2. On Windows, confirm `bash -lc 'uname -s'` returns `MINGW`, `MSYS`, or `CYGWIN`; WSL Bash is not supported.
3. Treat `/usr/bin/env: 'bash\r': No such file or directory` as a launcher line-ending or wrong-Bash-runtime issue, not a HaloPSA API issue.
4. Treat `codex.exe` under `WindowsApps` returning `Access is denied` as a local Codex/PATH issue.
5. On the ITECS Mac, confirm `/opt/homebrew/bin/op-itecs` can read the configured fields without printing their values. Stop on failure; do not fall back to plain `op`.
