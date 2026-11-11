# Work notes and time entries

Write a concise note from the supplied work, actual result and outstanding steps. For a standalone note, use `halopsa.ticket_actions.create_private_note` unless the technician requests a public note. A time entry already includes its own private note. Add a separate note when requested.

Pass `minutes` for an exact duration such as 1:07. Ask for missing duration and preserve the actual result. Use the named `charge_rate` directly, and pass an entry-level `contract_ref` or `contract_id` when the work belongs to a different contract. For explicitly uncontracted work use `clear_contract: true`. Read [ticket billing](../../ticket-billing-readiness/SKILL.md) when the rate or contract needs resolving.

Use the connector's `duplicate` result to report the existing action. Use `halopsa.ticket_actions.update` for an existing action and `halopsa.ticket_actions.delete` for a requested removal. Look up the action only when its ID is unknown. Report the recorded duration, rate and entry contract from readback when logging time.
