---
name: service-desk-work-log
description: Use when recording completed technician work as a HaloPSA note, time entry, or both from a conversational description.
---

# Record completed service-desk work

Use the ticket/project context already supplied and read the relevant record and recent actions. Resolve discoverable names and IDs with the available tools. Turn the technician's description into a clear work note containing the observed issue, actions taken, result and outstanding work. Preserve technical details and do not invent completion or elapsed time.

For a note, use `halopsa.ticket_actions.create_private_note` by default; use the public-note path when the technician requests client-visible content. For logged time, use `halopsa.ticket_actions.create_time_entry`, resolving charge-rate details from verified context and asking for duration only when it is missing. A time entry already contains a private work note, so do not create a duplicate note unless requested.

Follow the installed HaloPSA runtime skill and the existing tool's preview/confirmation fields. Do not add a second confirmation layer. Read back the resulting action and report the ticket, recorded duration when relevant, and outcome.
