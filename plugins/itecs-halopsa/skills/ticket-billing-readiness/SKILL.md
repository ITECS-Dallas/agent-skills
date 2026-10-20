---
name: ticket-billing-readiness
description: Use when a HaloPSA ticket or project must be ready to bill - link, switch or clear its contract, pick the billing type (charge rate), log billable time against the right contract, correct or remove a logged time entry, review logged time, or check remaining contract hours.
---

# Ticket billing readiness

A ticket or project bills against the contract linked on it. Time logged on a record with no contract draws from nothing, and the wrong charge rate bills the wrong amount, so settle both before logging time. This skill uses only the typed HaloPSA tools; do not use the browser for contract links.

## 1. Read the billing state

Call `halopsa.tickets.get` (or `halopsa.projects.get`) with `compact: true`. Read the `billing` block (`ticket_context.billing` for a ticket):

- `contract_linked`, `contract_ref`, `contract_id` - what the record bills to now.
- `eligible_contracts` - the contracts HaloPSA offers for the record, each with its billing description and remaining hours.
- `warnings` - for example "No contract is linked", or a record marked non-billable.

For prepay totals, used and remaining hours, read `halopsa.contracts.get` with `include_details: true` and `compact: true`. `halopsa.tickets.list` with `contract_id` shows what else bills to a contract.

## 2. Link, switch or clear the contract

Use `halopsa.tickets.update` or `halopsa.projects.update` with the `last_update` from the read you just made, and one of:

- `contract_ref` - the contract reference, for example `ACME-DEV`. It matches exactly among the record's own client's contracts; a near match is refused and the error lists the client's active contracts.
- `contract_id` - the contract id, when several active contracts share a reference.
- `clear_contract: true` - unlink.

The connector refuses a contract that belongs to another client, is inactive, has not started or has expired. The preview names the contract that will be linked, the one it replaces and any warning; surface the warnings. The write is read back and `result.readback.verified` reports whether HaloPSA applied it; if it differs, report the difference and do not retry.

Never guess a contract. If the request names one, use it. If it describes one ("the development contract") and exactly one eligible contract fits, use it and say which. If several fit, or none does, ask which. Creating or editing a contract record is a different operation (`halopsa.contracts.create` and `update`) and needs the `edit:contracts` scope; check with `halopsa.servers.list` and `include_status: true` before attempting it.

An explicit request that names the record and the contract authorizes `confirm: true`. Otherwise show the preview and accept one ordinary confirmation.

## 3. Choose the billing type

`halopsa.metadata.list` with kind `charge_rates` lists each billing type by name with the effective hourly rate; add `search`, `client_id` and `contract_id` to see the client and contract rates. Pass the name as `charge_rate` on the time entry. Use the exact name the technician gives; if it is ambiguous the error lists the choices. Use `No Charge` explicitly for included or non-billable work. Do not invent a charge rate when the technician did not say which one applies; offer the likely names with their rates.

## 4. Log time

Use `halopsa.ticket_actions.create_time_entry` with the duration the technician supplied (never estimate it), the work note, and `charge_rate`. The preview shows the resolved charge rate and hourly rate and warns when the record has no contract or no charge rate; fix those first (steps 2 and 3), then confirm. The entry is read back and compared; report from the readback.

## 5. Correct logged time

Change an entry that is already logged with `halopsa.ticket_actions.update` instead of logging a second entry for the same work. Take its id from `halopsa.time_entries.list` (`action_number`) or `halopsa.ticket_actions.list` with `time_entries_only: true`. Supply only what changes:

- `hours` and `nonbillable_hours` (`0` makes the whole entry billable);
- `charge_rate` by exact name, or `charge_rate_id` (`0` is No Charge);
- `contract_ref` or `contract_id` to bill the entry against another contract of the ticket's client (written as HaloPSA's `action_contract_id`);
- `performed_at`, `note`, `hidden_from_user` or anything else through `extra_fields`.

The preview shows each field's current value beside the new one. HaloPSA recalculates the entry's billing when it is saved: a billable rate on a pre-pay contract deducts the hours, and No Charge releases them. Read `halopsa.contracts.get` with `include_details: true` afterwards to confirm the balance. Warnings about an entry that is processed, invoiced or locked from recalculation are informational. To remove a duplicate or mistaken entry, use `halopsa.ticket_actions.delete`.

## 6. Review time and explain changes

- `halopsa.time_entries.list` shows an agent's logged time for a date window (default: my time today) with charge type names and totals by charge type and ticket.
- `halopsa.ticket_actions.list` with `time_entries_only: true` shows one record's entries.
- `halopsa.tickets.audit` shows who changed a field and when, for example when a contract was linked or cleared.

When reviewing a day or week, check each ticket that has time with step 1 and list those with no linked contract.

## Limits

- Time already logged on the record may keep its previous contract after a change. Check existing entries (step 6) and move them with `halopsa.ticket_actions.update` and `contract_ref` when they should follow the new contract.
- The connector cannot adjust a contract's balance, issue credits or invoice. Say so rather than working around it.
- Scopes: linking a contract, logging time and correcting or deleting entries need `edit:tickets`; `halopsa.time_entries.list` needs `read:timesheets`.
