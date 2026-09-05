---
name: vcenter-mcp
description: Use when developing GO-MCP vCenter inventory, VM tag allocation, or monthly hosting billing extraction.
---

# vCenter development and billing

For installed inventory lookups, use ITECS vCenter's live tools and runtime skill. For packaged Excel/JSON extraction and consolidated hosting audits, use ITECS Billing Audit. No source checkout is needed for those installed workflows.

When changing GO-MCP, read its current `skills/vcenter-mcp/SKILL.md` and `connectors/vcenter/README.md`. The source artifact is `vcenter-billing-audit-v2`; preserve exact disk bytes and storage tiers, stable VM identity, Client and BillingScope evidence, and source-quality evidence.

The monthly hosting command is `make hosting-audit`; staged targets are `hosting-audit-collect`, `hosting-audit-mapping-review`, and `hosting-audit-finalize`. Pass the requested `MONTH`; review and finalization reuse `SOURCE_RUN_ID` and a `RECONCILIATION_ID` offline.

Standalone developer extraction from `connectors/vcenter`:

```bash
go run ./cmd/billing-report -config ~/.codex/vcenter-mcp/config.json -month YYYY-MM -out-dir /absolute/output/path
```

JSON is the default. Add `-json-only=false` for the diagnostic workbook. Use the requested month, or state the current-month assumption and proceed. Operator identity mappings belong to the reconciliation crosswalk, not the source connector. Keep credentials in the existing local config and report the requested evidence with its source and timestamp.
