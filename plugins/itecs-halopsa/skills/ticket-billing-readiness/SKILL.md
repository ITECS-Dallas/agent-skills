---
name: ticket-billing-readiness
description: Use when setting a HaloPSA ticket or project contract, choosing a charge rate or entry contract, correcting or removing logged time, or reviewing time and remaining prepay hours.
---

# Ticket billing readiness

- For a new time entry, start with `halopsa.ticket_actions.create_time_entry`. Pass the named `charge_rate` and the intended entry `contract_ref`, `contract_id` or `clear_contract` directly when supplied. A record-level contract change is a separate request.
- For a requested record link, start with `halopsa.tickets.get` or `halopsa.projects.get` for the current snapshot. For an identified existing action, use `halopsa.ticket_actions.update` or `delete`. For an unknown action on a known ticket, use `halopsa.ticket_actions.list` with `time_entries_only: true` and `compact: true`. Use `halopsa.time_entries.list` for timesheet context and `halopsa.contracts.get` for a prepay balance.
- Use `halopsa.metadata.list` with `kind: charge_rates` when choosing or resolving a rate. For shorthand such as “level one,” search the applicable `Level 1` or `Lvl 1` label with the relevant `contract_id` and use the exact returned name.

See [billing procedures](references/billing.md) for linking, [named rates](references/billing.md#3-choose-the-billing-type), [entry overrides](references/billing.md#4-log-time) and [time corrections](references/billing.md#5-correct-logged-time). Execute with `confirm: true` once the requested inputs are resolved.
