---
name: sales-opportunity-workflow
description: Use when creating or advancing a HaloPSA Project Opportunity or recording related prospect, contact, sales notes, SOW and approval evidence.
---

# HaloPSA sales opportunities

For a new inquiry, start with `halopsa.clients.list` if the prospect’s client record is unknown. For an existing opportunity whose ID is unknown, use `halopsa.opportunities.list`. With the record already resolved, start with the requested note, attachment, update or workflow action and reuse its known IDs.

Read [opportunity procedures](references/opportunities.md) for prospect creation, tenant-required fields, attachment hashes and stage transitions. Reuse the technician’s authorization for the requested action and verify its readback.
