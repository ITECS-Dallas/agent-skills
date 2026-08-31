---
name: halopsa-mcp
description: Use when looking up live HaloPSA records or performing an explicitly approved private/public note, time entry, ticket write, or project write through the ITECS HaloPSA MCP plugin.
---

# HaloPSA MCP

## Purpose

Use the bundled HaloPSA MCP server for live lookup workflows and tightly governed writes to one exact ticket or project at a time.

## Required Boundaries

- Keep all activity read-only unless the user explicitly requests one exact supported mutation and approves its complete preview.
- Default notes to `halopsa.ticket_actions.create_private_note`. Re-read the exact ticket/project, preview the complete internal note, and require `APPROVE HALOPSA PRIVATE NOTE <ticket-id>`. The tool hard-codes private visibility and disables email.
- Before a public note, re-read the exact ticket, verify its client and context, preview the complete note, identify it as public/client-visible, and obtain the workflow's exact approval phrase.
- Use only `halopsa.ticket_actions.create_public_note` with the approved ticket ID and note body and `confirm_public: true`. Never substitute a direct HTTP request or browser write.
- Before a time entry, re-read the exact ticket/project and preview the work note, total hours, nonbillable hours, charge-rate ID, and performed timestamp. Require `APPROVE HALOPSA TIME ENTRY <ticket-id>`. Time entries are private `Note` actions with email disabled.
- Before ticket creation, verify the exact client, site/user when supplied, ticket type, priority/team/agent when supplied, at least one category ID, positive impact and urgency values, summary, and details. Warn that tenant rules or workflows may still send notifications. Preview every field, including category, impact, and urgency, and obtain the exact phrase `APPROVE HALOPSA TICKET CREATE`; then call `halopsa.tickets.create` once.
- Before a ticket field update, re-read the exact ticket, record `last_update`, preview every changed field, and require `APPROVE HALOPSA TICKET UPDATE <ticket-id>`. Pass the snapshot as `expected_last_update`; use the separate status tool for status.
- Before a status change or resolution, read the exact ticket and `halopsa.ticket_statuses.list`, preview the current and target status IDs and names, warn that tenant rules or workflows may activate, and obtain `APPROVE HALOPSA STATUS CHANGE <ticket-id> TO <new-status-id>`. Pass the immediately read current status as `expected_current_status_id` and call `halopsa.tickets.update_status` once.
- Before project creation, verify and preview at least one category ID plus positive impact and urgency values. For a project create, field update, or status update, use the equivalent `halopsa.projects.*` tool. Follow its exact approval phrase, use `last_update` for field patches, and revalidate current/allowed statuses for status changes.
- After a successful or ambiguous call, independently read back the ticket or actions. Never automatically retry an ambiguous write.
- Do not email, reply to a user, set recipients/subjects, choose an arbitrary action outcome, add attachments, delete records, or bypass the typed tools with direct API/browser writes. Those operations are not exposed.
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
- `halopsa.projects.create` - create one approved project with typed routing, required category/impact/urgency, dates, milestone, and budget fields.
- `halopsa.projects.update` - update supported project fields after `last_update` revalidation.
- `halopsa.projects.update_status` - change one project's status after current/allowed-status revalidation.
- `halopsa.tickets.list` - list tickets with client, site, user, agent, status, priority, team, text, date, and pagination filters.
- `halopsa.tickets.get` - get one ticket by ID, optionally including recent actions/notes.
- `halopsa.ticket_statuses.list` - list ticket statuses, optionally narrowed to an exact ticket or ticket type.
- `halopsa.ticket_actions.list` - list ticket actions/notes for a specific ticket.
- `halopsa.ticket_actions.create_public_note` - add one public/client-visible note to an exact ticket after explicit approval; no email, status, time, attachment, or private-note side effects.
- `halopsa.ticket_actions.create_private_note` - add one internal/private, non-email note to an exact ticket or project; this is the default note path.
- `halopsa.ticket_actions.create_time_entry` - log one private, non-email time entry against an exact ticket or project.
- `halopsa.tickets.create` - create one approved ticket with explicit routing, required category/impact/urgency, and content fields; one attempt only.
- `halopsa.tickets.update` - update supported ticket routing/content/category/parent fields after `last_update` revalidation.
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

On macOS, run from the installed plugin directory:

```bash
./scripts/configure-halopsa-mcp-macos.sh --technician "Exact Technician Name"
```

The plugin launcher also honors:

```bash
HALOPSA_MCP_CONFIG=/absolute/path/to/config.json
```

Never store credentials in this plugin repository.

On Windows 11, run in PowerShell from the installed plugin directory:

```powershell
.\scripts\configure-halopsa-mcp-windows.ps1 -TechnicianName "Exact Technician Name" -ItecsAccount "ITECS-1PASSWORD-ACCOUNT-SHORTHAND"
```

Both scripts require the exact per-technician `GO-MCP HaloPSA <Technician> Read Write` item, validate its six expected fields and live OAuth response, and write command references only. Do not copy credential values into `config.json`; do not use another technician's item. On macOS, never fall back from `/opt/homebrew/bin/op-itecs` to plain `op`.

## Windows Startup Troubleshooting

If HaloPSA tools are not callable, check startup layers before checking vendor auth:

1. Confirm the plugin is installed and the Codex thread was started after install.
2. On Windows, confirm `bash -lc 'uname -s'` returns `MINGW`, `MSYS`, or `CYGWIN`; WSL Bash is not supported.
3. Treat `/usr/bin/env: 'bash\r': No such file or directory` as a launcher line-ending or wrong-Bash-runtime issue, not a HaloPSA API issue.
4. Treat `codex.exe` under `WindowsApps` returning `Access is denied` as a local Codex/PATH issue.
5. On the ITECS Mac, confirm `/opt/homebrew/bin/op-itecs` can read the configured fields without printing their values. Stop on failure; do not fall back to plain `op`.
