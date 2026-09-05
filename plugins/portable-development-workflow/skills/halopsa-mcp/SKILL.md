---
name: halopsa-mcp
description: Use when developing GO-MCP HaloPSA source extraction or working with recurring-invoice artifacts and billing reconciliation. Live service-desk operations use the installed ITECS HaloPSA runtime skill.
---

# HaloPSA source and billing workflow

GO-MCP owns connector implementation. ITECS HaloPSA supplies the installed live tools for tickets, projects, notes, time, Start Work, email, contracts, invoices and purchase orders. Use its current runtime catalog for operations rather than inferring capabilities from this development skill.

For development, read GO-MCP's `skills/halopsa-mcp/SKILL.md` and connector README in the selected checkout. For an installed monthly workflow, use the ITECS Billing Audit plugin's `billing-reconciliation` skill and packaged commands.

The source extractor writes correlated `halopsa-recurring-invoices-v3` and `halopsa-client-snapshot-v1` JSON artifacts. It does not refresh operator mappings. The workflow owns `billing-client-crosswalk-v2`; mapping review and finalization work offline against a sealed source run. A mapping correction uses a new reconciliation attempt against the same source bytes.

From a GO-MCP checkout:

```bash
MONTH=YYYY-MM make hosting-audit-collect
MONTH=YYYY-MM SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID make hosting-audit-mapping-review
MONTH=YYYY-MM SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID make hosting-audit-finalize
```

For standalone extraction, run `go run ./cmd/billing-report -config ~/.codex/halopsa-mcp/config.json -month YYYY-MM -out-dir /absolute/output/path` from `connectors/halopsa`. JSON is the default; add `-json-only=false` for the diagnostic workbook.

Use the requested month, or state the current-month assumption and proceed when none is supplied. Resolve required facts from available context. Keep credentials in the existing command-backed runtime config; do not display their values. Report artifact locations and the evidence relevant to the user's question.
