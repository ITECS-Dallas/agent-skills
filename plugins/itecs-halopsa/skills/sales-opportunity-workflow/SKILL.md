---
name: sales-opportunity-workflow
description: Use when recording a new sales inquiry or a sales update in HaloPSA - prospect client and contact, Project Opportunity, sales notes, cheat sheets, SOW and approval evidence, and opportunity workflow stages - through the typed tools instead of the browser.
---

# HaloPSA sales opportunity workflow

Every new sales inquiry gets a HaloPSA Project Opportunity, and each sales update (emails, meeting summaries, cheat sheets) is added to it as an internal note. The sales document library keeps generating and owning proposals, SOWs and cheat sheets; HaloPSA holds the opportunity record, owner, stage and evidence for the handoff to delivery.

Prefer the typed tools below. Use other available routes when the technician requests work the connector does not yet support, preserving the existing credential workflow.

## Before creating anything

Search first and reuse what exists: `halopsa.clients.list` for the company, `halopsa.metadata.list` kind `users` with the contact's email, and `halopsa.opportunities.list` for the client. `halopsa.tickets.list` does not return opportunities. The create tools also refuse an existing client name, contact email or open opportunity summary; treat that refusal as "reuse the existing record".

## Sequence for a new inquiry

1. **Prospect client** - `halopsa.clients.create` with the company name, `top_level_id` (metadata kind `top_levels`, normally Areas), `relationship_ids` (kind `client_relationships`, Prospect), `exclude_from_accounting: true`, and the website, reference and main site address when known.
2. **Contact** - `halopsa.users.create` with first and last name, email, phone, mobile and job title. HaloPSA sends no welcome or portal email.
3. **Opportunity** - resolve the Project Opportunity type with kind `ticket_types` and `halopsa.agents.me` for the sales owner, then `halopsa.opportunities.create` with the client, contact, `agent_id`, summary and details. Opportunities need no support category, impact or urgency. The preview lists the type's fields; supply everything in `missing` (the tenant marks fields such as Target Date mandatory) and use names from `fields[].choices` for selections. Ask the requester for a missing value instead of inventing one.
4. **Sales history** - `halopsa.ticket_actions.create_private_note` on the opportunity for each email, call or meeting summary and cheat sheet.
5. **Documents** - `halopsa.attachments.upload` for cheat sheets, the exact approved SOW version and the customer's approval evidence. Upload the reviewed file from the sales library and pass the preview's `expected_sha256`. Attachments are internal; HaloPSA end users do not see them.

## Advancing the opportunity

Use `halopsa.opportunities.execute_workflow_action` with an `outcome_id` from `halopsa.ticket_outcomes.list` for the opportunity and the `last_update` from an immediate read. The preview shows the step transition and the action's fields, including mandatory members of field groups, with choices. Typical Project Opportunity actions are Contact Made, Scope Project, Complete Internal Review, Record SOW Sent, Record Customer Approval, Accept Delivery Handoff and Lost. Create Delivery Project is a HaloPSA system action; do it in HaloPSA or create the delivery project with the project tools.

Change potential value, target date or contact fields with `halopsa.opportunities.update`. Fields that are read-only on the opportunity screen change only through the workflow action that presents them.

## Authorization and evidence

- An explicit technician request authorizes the requested client, contact, opportunity, document, note or workflow operation. Use the preview to resolve tenant requirements, then execute with `confirm: true` under that authorization; do not request a second confirmation. Ask only for missing required facts or an expanded action that was not requested.
- Each write is attempted once. Report completion from the tool's `readback`. If it shows a mismatch or error, report it and read the record; never retry blindly.
- These writes need the technician's HaloPSA credential to include `read:crm` and `edit:crm` (opportunities) and `edit:customers` (clients and contacts). A permission error means the credential or role needs updating; stop and report it.
- Never put credentials, government IDs, bank or card numbers, or health records in notes or attachments.
