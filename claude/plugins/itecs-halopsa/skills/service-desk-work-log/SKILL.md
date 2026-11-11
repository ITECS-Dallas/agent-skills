---
name: service-desk-work-log
description: Use when turning completed HaloPSA technician work into a note or a new time entry from the technician’s description.
---

# Record completed work

On a known ticket or project, use `halopsa.ticket_actions.create_private_note` for an internal note or the public note tool when requested. For a new time entry with no specified rate, ask which rate to use and wait for the answer. Once supplied, use `halopsa.ticket_actions.create_time_entry` with the duration, exact rate and requested contract. Verify the saved rate from readback. The time entry already carries the private work note.

Execute the authorized action with `confirm: true` once inputs are known. Use [work log details](references/work-log.md) for exact minutes, duplicates and readback. Use [ticket billing](../ticket-billing-readiness/SKILL.md) for contract decisions or corrections to existing time.
