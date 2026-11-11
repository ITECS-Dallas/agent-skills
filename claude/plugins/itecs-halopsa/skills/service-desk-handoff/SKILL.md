---
name: service-desk-handoff
description: Use when summarizing HaloPSA tickets or projects for a technician briefing, shift handoff or next-action review.
---

# Service-desk handoff

Start with `halopsa.tickets.get` or `halopsa.projects.get` for known IDs. Use the relevant `.list` tool for a queue or search. Read the recent actions with `halopsa.ticket_actions.list`, paging when the handoff needs more history. Use `compact: true` where available.

Follow the [handoff fields](references/handoff.md) for the summary and billing or client-conversation evidence. Write to HaloPSA when the user requests that action.
