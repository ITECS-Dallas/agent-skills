---
name: halopsa-mcp
description: Use when finding live HaloPSA records, creating a ticket, or performing a direct technician action such as assignment, Start Work, status, email, invoices, contracts, or client, contact, site and asset edits.
---

# HaloPSA technician operations

Use the installed `halopsa.*` tools and reuse the exact record and facts already supplied. To create a ticket, start with `halopsa.tickets.create` using the facts supplied. Resolve only missing tenant fields or routing. Read back the created ticket with `halopsa.tickets.get`, `compact: true` and `include_actions: false`. Add `ticketidonly: true` when an existence check is sufficient. For a ticket lookup or update requiring the current record, start with `halopsa.tickets.get` and `compact: true`. Start a project lookup with `halopsa.projects.get`, a search without an ID with the relevant `.list` tool, and an identified direct action with its typed tool when the required inputs are known.

Use `confirm: true` for the requested write. Use a preview when requested or needed to resolve inputs or effects. Ask only for required facts or a material choice the request and available records cannot resolve. Preserve draft requests, sender routing, snapshot requirements and readback. Reconcile an ambiguous write before any retry.

- Use [record and action details](references/operations.md) for tool selection, exact outcomes, concurrency, invoices or special fields.
- For completed work, time corrections or contract changes, use [work logging](../service-desk-work-log/SKILL.md) or [ticket billing](../ticket-billing-readiness/SKILL.md).
- For sales records, ticket summaries or optional client help, use [sales opportunities](../sales-opportunity-workflow/SKILL.md), [handoff](../service-desk-handoff/SKILL.md) or [client troubleshooting](../service-desk-client-troubleshooting/SKILL.md).
- For setup and connector version, see the [plugin guide](../../README.md). `halopsa.servers.list` with `include_status: true` shows the loaded version and scope coverage.
