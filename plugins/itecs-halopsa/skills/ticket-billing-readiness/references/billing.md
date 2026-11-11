# Ticket billing readiness

A new time entry inherits the ticket or project contract by default. A single entry can instead use another active contract of the same client or no contract. Change the record link only when the technician requests that change. Use the typed tools with the existing credentials and verify the resulting entry or record.

## 1. Read the billing state

When the linked contract or the record-level billing state matters, call `halopsa.tickets.get` or `halopsa.projects.get` with `compact: true`. Read `ticket_context.billing` for a ticket or `billing` for a project.

- `contract_linked`, `contract_ref`, `contract_id` - what the record bills to now.
- `eligible_contracts` - the contracts HaloPSA offers for the record, each with its billing description and remaining hours.
- `warnings` - for example "No contract is linked", or a record marked non-billable.

For prepay totals, used and remaining hours, read `halopsa.contracts.get` with `include_details: true` and `compact: true`. `halopsa.tickets.list` with `contract_id` shows what else bills to a contract.

## 2. Link, switch or clear the contract

Use `halopsa.tickets.update` or `halopsa.projects.update` with the current `last_update` as `expected_last_update` and one of these fields.

- `contract_ref` - the contract reference, for example `ACME-DEV`. It matches exactly among the record's own client's contracts; a near match is refused and the error lists the client's active contracts.
- `contract_id` - the contract id, when several active contracts share a reference.
- `clear_contract: true` - unlink.

The connector refuses a contract that belongs to another client, is inactive, has not started or has expired. When needed, use the preview to inspect the resolved contract, the previous contract and any warnings. The write is read back and `result.readback.verified` reports whether HaloPSA applied it; if it differs, report the difference and do not retry.

Never guess a contract. If the request names one, use it. If it describes one ("the development contract") and exactly one eligible contract fits, use it and say which. If several fit, or none does, ask which. Creating or editing a contract record is a different operation (`halopsa.contracts.create` and `update`) and needs the `edit:contracts` scope. Use `halopsa.servers.list` with `include_status: true` when diagnosing scope coverage.

An explicit request to perform the billing work authorizes `confirm: true` once the contract is resolved from the request and applicable records. Ask only when the contract choice remains ambiguous; do not require the technician to repeat an already authorized action.

## 3. Choose the billing type

Pass the exact named `charge_rate` directly to the time tool. Use `halopsa.metadata.list` with kind `charge_rates` only to discover a missing rate, review the effective hourly rate, or resolve ambiguity. Supply `search`, `client_id` and `contract_id` when applicable so contract-limited named rates are included. For “level one,” search for the applicable `Level 1` or `Lvl 1` label within the relevant contract’s rates and use the exact returned name. Use `No Charge` when that is the intended rate. Ask if the correct rate remains unresolved.

## 4. Log time

Use `halopsa.ticket_actions.create_time_entry` with the supplied duration, work note and named `charge_rate`. Pass `contract_ref` or `contract_id` when this entry should bill to another active contract of the ticket's client. Pass `clear_contract: true` when it should bill to no contract. Otherwise the entry inherits the record's contract. A missing record link does not prevent use of an explicit entry contract. A rate limited to another contract needs the correct entry-level contract or a different rate.

Use a preview if it helps choose inputs or inspect effects. The preview shows the entry's contract beside the ticket's and flags a rate that belongs to a different contract. The readback verifies the duration, rate and entry contract. If HaloPSA ignored the contract on create, `result.contract_correction` reports the one update the connector attempted to set it. Report the verified result and any unresolved discrepancy.

## 5. Correct logged time

Change an entry that is already logged with `halopsa.ticket_actions.update` instead of logging a second entry for the same work. Use the action ID when supplied. For a known ticket, find it with `halopsa.ticket_actions.list` and `time_entries_only: true, compact: true`. For a timesheet lookup, `halopsa.time_entries.list` returns it as `action_number`. Supply only what changes:

- `hours` and `nonbillable_hours` (`0` makes the whole entry billable);
- `charge_rate` by exact name, or `charge_rate_id` (`0` is No Charge);
- `contract_ref` or `contract_id` to bill the entry against another contract of the ticket's client, or `clear_contract: true` for no contract (written as HaloPSA's `action_contract_id`; a contract of another client or an inactive one is refused);
- `performed_at`, `note`, `hidden_from_user` or anything else through `extra_fields`.

The preview shows each field's current value beside the new one. HaloPSA recalculates the entry's billing when it is saved: a billable rate on a pre-pay contract deducts the hours, and No Charge releases them. Read `halopsa.contracts.get` with `include_details: true` afterwards to confirm the balance. Warnings about an entry that is processed, invoiced or locked from recalculation are informational. To remove a duplicate or mistaken entry, use `halopsa.ticket_actions.delete`.

## 6. Review time and explain changes

- `halopsa.time_entries.list` shows an agent's logged time for a date window (default: my time today) with charge type names and totals by charge type and ticket.
- `halopsa.ticket_actions.list` with `time_entries_only: true` shows one record's entries.
- `halopsa.tickets.audit` shows who changed a field and when, for example when a contract was linked or cleared.

When reviewing a day or week, check each ticket that has time with step 1 and list those with no linked contract.

## Limits

- Time already logged on the record may keep its previous contract after a change. Check existing entries (step 6) and move them with `halopsa.ticket_actions.update` and `contract_ref` when they should follow the new contract.
- Use `halopsa.invoices.create`, `approve` or `sync_to_accounting` for supported invoice operations. For a direct balance adjustment, use an available authorized route that supports it.
- Scopes: linking a contract, logging time and correcting or deleting entries need `edit:tickets`; `halopsa.time_entries.list` needs `read:timesheets`.
