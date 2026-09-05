---
name: vcenter-mcp
description: Use when looking up live vCenter VMs, Client/BillingScope tags, resource allocations, or hosting inventory through the installed ITECS vCenter plugin.
---

# vCenter operations

Use the bundled MCP tools directly for inventory requests. A technician does not need Go or a GO-MCP checkout.

- `vcenter.servers.list`: configured targets.
- `vcenter.vms.list`: VM identities, allocation, tags and storage evidence.
- `vcenter.inventory.summary`: counts, power state, resources and tag grouping.
- `vcenter.billable_report` and `vcenter.monthly_report`: Markdown billable allocation reports.

Resolve the requested server and client from available context and returned IDs/tags. Preserve CPU, memory, total provisioned storage, mechanical, SSD and unknown storage separately. Identify the collection time and distinguish source evidence from inferred client identity.

For an Excel/JSON source report, use ITECS Billing Audit's packaged `scripts/run-source-report vcenter -month YYYY-MM -json-only=false -out-dir /absolute/output/path`. For consolidated hosting reconciliation use its `billing-reconciliation` skill. The original GO-MCP developer CLI remains available.

Use the requested month, or state the current-month assumption and proceed. Existing configuration is `~/.codex/vcenter-mcp/config.json`, with `VCENTER_MCP_CONFIG` as an override. Keep credential values out of output. Use `scripts/doctor` in this plugin for optional startup diagnostics; its MCP discovery option lists tools without running an inventory query.
