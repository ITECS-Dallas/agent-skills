# Record and action details

Use `halopsa.agents.me` when the authenticated technician must be resolved and `halopsa.metadata.list` for unknown names or IDs. Reuse resolved metadata and use `compact: true` where supported. Pass additional standard fields by their API names in `extra_fields` and custom fields by ID in `custom_fields` when the tool supports them.

- For status, Start Work, closure, screenshot uploads and ticket contact email, use [ticket actions](ticket-actions.md).
- For ticket or project creation, resolve category, impact and urgency with tenant metadata and the facts supplied. The sales opportunity workflow has its own tenant fields and preview.
- Where required, send the current `last_update` or status and report from readback. `structuredContent.error.code: "ticket_changed"` and `write_attempted: false` on ticket email or status prove rejection before the write. Refresh and reconcile under the existing authorization. Ambiguous transport or post-write results require readback before any retry.
- If a typed tool cannot perform the requested operation, use another authorized route that supports it with the existing credentials and permissions.
- For an entry's billing contract and charge rate, see [ticket billing](../../ticket-billing-readiness/SKILL.md). To link the record itself, use the ticket or project update tool only when that record-level change is requested.

## Tool details

- `halopsa.servers.list` - list configured HaloPSA targets without exposing credentials; `include_status: true` adds the connector version, the authenticated agent, configured scopes and which tool groups they cover, and `check_updates: true` adds whether a newer plugin release exists.
- `halopsa.clients.list` - list clients with search, active/inactive, and pagination filters.
- `halopsa.clients.get` - get one client by ID.
- `halopsa.invoices.list` - list invoices with client, date, payment, sent, and pagination filters.
- `halopsa.invoices.get` - get one invoice by ID.
- `halopsa.invoices.create` - preview or create one one-time invoice with lines, negative-price credit lines and optional `copy_from_recurring` lines. Pass an `idempotency_key` (for example `mdr-2026-10`); a rerun returns the invoice already created, and a live invoice with the same client, date and lines is reported as a `duplicate` unless `allow_duplicate` is set. It does not send or sync the invoice. Needs `edit:invoices`.
- `halopsa.invoices.sync_to_accounting` - push one final invoice to QuickBooks Online, as the invoice screen's Sync button does. An already-synced, unchanged invoice is `already_done` unless `resync` is set. Invoices that are voided, have no QBO company, or have pending or rejected approval are refused. Needs `edit:invoices`.
- `halopsa.invoices.approve` - approve or reject (`decision`) an invoice awaiting the connector agent's approval. Needs `edit:invoices`.
- `halopsa.recurring_invoices.list` - list recurring invoices with client, date, sent, ready-for-invoicing, and pagination filters.
- `halopsa.recurring_invoices.get` - get one recurring invoice by ID.
- `halopsa.contracts.list` - list client contracts with client, site, type, renewal, and pagination filters; each carries its Agreement Subtype and billing description labels.
- `halopsa.contracts.get` - get one client contract by ID; detailed reads include prepay totals, used and remaining balance.
- `halopsa.contracts.create` - preview or create one client contract with dates, type, status, billing, invoice, and rolling fields.
- `halopsa.contracts.update` - preview or update contract fields, including any other field through `extra_fields`, after `last_modified` revalidation.
- `halopsa.purchase_orders.list` - list purchase orders with open/closed status, supplier, client, ticket, search, and pagination filters.
- `halopsa.purchase_orders.get` - get one purchase order by ID.
- `halopsa.projects.list` - list projects with client, site, agent, status, milestone, team, text, date, and pagination filters.
- `halopsa.projects.get` - get one project by ID.
- `halopsa.projects.create` - preview or create one project with typed routing, required category/impact/urgency, dates, milestone, and budget fields.
- `halopsa.projects.update` - update project fields, including the billing contract, `custom_fields` and any other field through `extra_fields`, after `last_update` revalidation.
- `halopsa.projects.update_status` - change one project's status after current/allowed-status revalidation under existing task authorization.
- `halopsa.tickets.list` - list tickets with client, site, user, agent, status, priority, team, text, date, and pagination filters.
- `halopsa.tickets.get` - get one ticket with additional agents, team/queue, workflow, native/custom change plans and billing context (linked contract, offered contracts with remaining hours, warnings), optionally including recent actions/notes. `compact: true` is about 95% smaller.
- `halopsa.ticket_statuses.list` - list ticket statuses, optionally narrowed to an exact ticket or ticket type.
- `halopsa.ticket_actions.list` - list ticket actions/notes for a specific ticket, optionally narrowed to conversation/public actions or a date window, with email HTML when needed. Leave `agent_only` false when reading client replies.
- `halopsa.ticket_outcomes.list` - list tenant-configured action outcomes available for an exact ticket or explicit state.
- `halopsa.ticket_outcomes.get` - get one configured outcome and its effects, optionally resolved for an exact ticket.
- `halopsa.ticket_actions.start_work` - preview or execute the one exact available Start Work outcome under existing task authorization with `last_update` revalidation.
- `halopsa.ticket_actions.resolve` - run the native workflow Resolve or Close action with the resolution note and explicit Email User choice, then verify the action and resulting ticket status.
- `halopsa.ticket_actions.send_email` - preview or send one ticket email. Omit `to` and `outcome_id` for the designated contact through Email User. Optional `email_template_id` selects a template for this message only; custom IDs may be negative. Omit it to keep the action's default template and signature behavior.
- `halopsa.ticket_actions.create_public_note` - add one public/client-visible note to an exact ticket under the technician's existing request; no email, status, time, attachment, or private-note side effects.
- `halopsa.ticket_actions.create_private_note` - add one internal/private, non-email note to an exact ticket or project; this is the default note path. A note already on the ticket with the same text is returned as a `duplicate` and not posted again; never pass `allow_duplicate` unless the technician wants a second copy.
- `halopsa.ticket_actions.create_time_entry` - log one private, non-email time entry against an exact ticket or project. `minutes` sets the duration exactly; hours are rounded to the whole minute HaloPSA stores. `charge_rate` resolves a billing type by name, including rates limited to the entry's contract. Ask for a missing rate and wait before posting new time. The entry bills to the ticket's linked contract unless `contract_ref` or `contract_id` names another contract of the ticket's client, or `clear_contract` bills it to no contract. The preview shows the entry's contract beside the ticket's and warns when no contract is linked, when the entry's contract differs from the ticket's, or when the charge rate is limited to a different contract. An entry already logged for the same work (same duration at the same Date Done, or with the same note that day, by anyone) is returned as a `duplicate` and not logged again. Verify the saved rate, exact minutes and chosen contract from readback. If HaloPSA ignored the contract on create, one update sets it and `contract_correction` reports it.
- `halopsa.tickets.create` - preview or create one ticket with explicit routing, required category/impact/urgency, and content fields; one attempt only.
- `halopsa.tickets.update` - update ticket routing/content/category/parent fields, the billing contract (`contract_ref`, `contract_id` or `clear_contract`), `custom_fields` and any other field through `extra_fields` after `last_update` revalidation; the preview shows the contract and warnings and the write is read back.
- `halopsa.tickets.update_status` - change one exact ticket's status only after current-status revalidation using the existing task authorization; one attempt only. A ticket already in the requested status is reported `already_done` without writing; after a change the status is read back.

- `halopsa.opportunities.list` - list the opportunity area (not returned by `halopsa.tickets.list`) by client, contact, agent, status, type and summary.
- `halopsa.opportunities.create` - preview or create one opportunity, such as a Project Opportunity, with the type's mandatory fields, contact defaults and duplicate-summary refusal; no category, impact or urgency.
- `halopsa.opportunities.update` - preview or update potential value, target date, company/contact fields and editable custom fields after `last_update` revalidation.
- `halopsa.opportunities.execute_workflow_action` - preview or run one workflow action available at the opportunity's current step, privately and without email or time; system actions are refused.
- `halopsa.clients.create` - preview or create one client with top level, relationship such as Prospect, website, reference, explicit accounting-integration exclusion and main site address; duplicate names are refused.
- `halopsa.users.create` - preview or create one client contact without a welcome or portal email; an existing email is refused.
- `halopsa.attachments.list` - list attachments on an exact ticket, opportunity or project.
- `halopsa.attachments.upload` - preview or upload a local file, including a screenshot, as an internal attachment. Pass the preview’s SHA-256 when uploading.

- `halopsa.metadata.list` - resolve agents, teams/queues, workflows, field definitions, sites, users, ticket types, categories, priorities, charge rates (named billing types with effective hourly rates), Agreement Subtype labels (`contract_subtypes`), billing descriptions, top levels, client relationships and any HaloPSA pick-list (`lookup` with `lookup_id`) using typed filters.
- `halopsa.agents.me` - identify the authenticated technician for my work and assignment requests; identity fields only unless `include_full` is set.
- `halopsa.tickets.audit` - list a ticket, project or opportunity's change history, newest first: who changed which field, from what, to what and when.
- `halopsa.time_entries.list` - list an agent's logged time for a date window from the timesheet, with charge type names and totals; defaults to my time today.
- `halopsa.ticket_actions.update` - edit an existing time entry or note: hours, non-billable hours, billing type, contract (`contract_ref`, `contract_id` or `clear_contract`; checked against the ticket's client), date done, note, visibility, importance, travel, mileage, reviewed and `extra_fields`; previews beside the current values, writes once and reads back, and HaloPSA recalculates billing and pre-pay.
- `halopsa.ticket_actions.delete` - delete one requested action from a ticket or project; an optional preview shows its content and readback confirms it is gone.
- `halopsa.clients.update` - edit a client's name, website, reference, notes, top level, account manager, active state, VIP, taxable, accounting exclusion, relationships, custom fields and `extra_fields`.
- `halopsa.users.update` - edit a contact's name, email, phones, job title, notes, client, site, active state and flags, custom fields and `extra_fields`; no email is sent.
- `halopsa.sites.update` - edit a site's name, phone, notes, time zone, active state, delivery and invoice address lines, custom fields and `extra_fields`.
- `halopsa.assets.create` - create an asset for a client with its type, site (defaults to the main site), inventory number, status, asset-type fields by id or name, custom fields and `extra_fields`.
- `halopsa.assets.update` - edit an asset's inventory number, notes, client, site, type, status, contract, supplier, active state, warranty, asset-type fields by id or name, custom fields and `extra_fields`.
- `halopsa.assets.list` - list assets (devices and configuration items) by client, site, assigned user or type, with search. A ticket's linked assets are in `halopsa.tickets.get` with `compact: true` as `linked_assets`.
- `halopsa.assets.get` - get one asset with its type-specific fields.

## Ticket context and change plans

For additional agents, the assigned queue, co-managed workflows or change-request
plans, use `halopsa.tickets.get` with its normal detailed response. Read
`ticket_context.assignment`, `workflow`, `change_management` and `custom_fields`.
Queue means the ticket's returned `team`/`team_id`. Custom Change Plan,
Implementation Plan, Test Plan and Backout Plan values may be populated while the
native plan fields are blank; inspect both and preserve field IDs when labels
repeat. Missing fields are unavailable, not confirmed empty. Discover tenant
workflow names with metadata kind `workflows` and native/custom plan definitions
with kind `fields` and search `plan`; use kind `teams` for queue IDs.

## Scopes and configuration

Sales opportunity scopes are `read:sales` and `edit:sales`. Customer, asset, contract and invoice writes require their corresponding `edit:*` scopes. Use the existing per-technician Automation Vault item and [platform setup](../../../README.md#runtime-configuration). Preserve the external config and managed `op-itecs` wrapper on macOS and Linux.

Asset updates merge the requested asset-type values into the current field list. Set a specific value to empty to clear it. A contract's writable `description` is stored in `note`; `refextra` is the computed reference. Missing requested or nested values in readback remain unverified.
