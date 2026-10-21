---
name: service-desk-work-log
description: Use when recording completed technician work as a HaloPSA note, time entry, or both from a conversational description.
---

# Record completed service-desk work

Use the ticket/project context already supplied and read the relevant record and recent actions. Resolve discoverable names and IDs with the available tools. Turn the technician's description into a clear work note containing the observed issue, actions taken, result and outstanding work. Preserve technical details and do not invent completion or elapsed time.

For a note, use `halopsa.ticket_actions.create_private_note` by default; use the public-note path when the technician requests client-visible content. For logged time, use `halopsa.ticket_actions.create_time_entry`, passing the billing type by name as `charge_rate` (list the names with `halopsa.metadata.list` kind `charge_rates`) and asking for duration only when it is missing. A time entry already contains a private work note, so do not create a duplicate note unless requested.

Before billable time, read the record with `halopsa.tickets.get` and `compact: true` and check `ticket_context.billing`. If no contract is linked, follow [ticket-billing-readiness](../ticket-billing-readiness/SKILL.md) to link the right one first; the time-entry preview repeats that warning. Never guess the contract or the charge rate.

An explicit request to record work, specified time or client-visible content authorizes `confirm: true`; do not ask again for that action. Honor a draft-only request. Use metadata lookup to resolve the technician and charge rate. The connector reads the entry back and compares its hours and charge rate; report the ticket, recorded duration, billing type, linked contract and outcome from that readback. HaloPSA stores time to the minute.
