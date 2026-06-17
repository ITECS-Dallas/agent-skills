---
name: pax8-mcp
description: Use when working on the GO-MCP Pax8 connector, Pax8 companies, subscriptions, licenses, vendor service billing facts, or Pax8-to-HaloPSA billing audit artifacts.
---

# Pax8 MCP

## Purpose

Build and operate a read-only Pax8 source connector that exports Pax8 billing facts for reconciliation against HaloPSA recurring invoice line items.

Read `docs/planning/pax8-connector-next-slice.md` before implementation.

## Required Boundaries

- Standardize repo names and paths as `pax8`, even if the prompt says "PACS 8".
- Do not print or commit Pax8 credentials, `.env` contents, local config JSON, tokens, or generated report contents.
- Use local runtime config under `~/.codex/pax8-mcp/`.
- Keep Pax8 actions read-only unless mutation is explicitly requested.
- Keep MCP stdout reserved for protocol traffic; write diagnostics to stderr or external files.
- Generated Pax8 workbooks and JSON sidecars belong in `reports/` and may be tracked only when the user explicitly approves sharing the audit snapshot through git.

## Connector Workflow

1. Verify the current Pax8 API or MCP access pattern from source-backed documentation before coding.
2. Reuse the repo-local Go MCP connector layout and official MCP Go SDK idioms.
3. Confirm local config exists without displaying secrets before live use.
4. Implement read-only tools first, with read-only annotations.
5. Keep source extraction inside `connectors/pax8`.
6. Write local Excel/JSON artifacts under `reports/`.
7. Leave cross-system variance detection in `workflows/billing-reconciliation`.

## Expected Billing Artifact Direction

Verified decision: the first report uses Pax8 REST companies, subscriptions, and products. It focuses on active or billable Pax8 subscriptions and includes enough fields to map back to HaloPSA:

- Pax8 company/customer identifiers and names
- subscription identifiers
- product/SKU identifiers and names
- quantity/license count
- status
- billing or term dates when available

Pax8 approved invoices, approved invoice items, and separate draft invoice items are included as source evidence after the subscription snapshot. Reconciliation still uses active subscriptions for Pax8 deltas until approved invoice-item field shape and service-line mapping behavior are verified.

## Run Command

Run the subscription snapshot report from `connectors/pax8`:

```bash
go run ./cmd/billing-report -config ~/.codex/pax8-mcp/config.json -month YYYY-MM
```

By default the command reads `../../reports/halopsa-client-mapping.json` when present so the Pax8 `Client Mapping` sheet can prefill HaloPSA client names and IDs. Pass `-client-mapping ""` only when a standalone Pax8 snapshot is required.

The command writes generated Pax8 workbook and JSON sidecar files under repo-root `reports/`:

```text
reports/pax8-subscriptions-YYYY-MM.xlsx
reports/pax8-subscriptions-YYYY-MM.json
```

The JSON schema is `pax8-subscriptions-v3`. Draft invoice items are pre-final evidence only and live under `draft_invoice_items`; do not treat them as billing truth.
