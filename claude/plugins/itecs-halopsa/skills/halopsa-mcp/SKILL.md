---
name: halopsa-mcp
description: Use for live HaloPSA ticket lookup and creation, assignment and status, Resolve or Close, screenshot attachments, email to a ticket contact, and direct edits to HaloPSA records.
---

# HaloPSA technician operations

Use the installed `halopsa.*` tools. For a ticket reference such as `ITECS-0095045`, pass the reference directly to `halopsa.tickets.get`, `compact: true`, and `include_actions: false`. Include recent actions when the technician asks for a review or the action history is needed. Search with the relevant `.list` tool when no exact ID is known.

- **Create a ticket.** Start with `halopsa.tickets.create` using the facts supplied. Resolve missing routing or tenant fields only. Read back the created ticket.
- **Mark In Progress, Start Work, Resolve or Close.** Use the ticket's current record and the matching [ticket action](references/ticket-actions.md).
- **Attach a screenshot or email the ticket contact.** Start with `halopsa.attachments.upload` or `halopsa.ticket_actions.send_email`. Read [ticket action details](references/ticket-actions.md) for the local file or recipient inputs.

Use `confirm: true` for the requested write. Use a preview when requested or needed to resolve inputs or effects. Ask only for required facts or a material choice the request and available records cannot resolve. Preserve draft requests, sender routing, snapshot requirements and readback. Reconcile an ambiguous write before any retry.

- Use [other HaloPSA operations](references/operations.md) for invoices, projects, special fields, and the full tool reference.
- For completed work, time corrections or contract changes, use [work logging](../service-desk-work-log/SKILL.md) or [ticket billing](../ticket-billing-readiness/SKILL.md).
- For sales records, ticket summaries or optional client help, use [sales opportunities](../sales-opportunity-workflow/SKILL.md), [handoff](../service-desk-handoff/SKILL.md) or [client troubleshooting](../service-desk-client-troubleshooting/SKILL.md).
- For setup and connector version, see the [plugin guide](../../README.md). `halopsa.servers.list` with `include_status: true` shows the loaded version and scope coverage.
