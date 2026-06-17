---
name: vcenter-mcp
description: Use when working on the GO-MCP vCenter connector, vCenter inventory, VM tags, billable client reporting, Excel audit workbooks, or live read-only vCenter validation.
---

# vCenter MCP

## Purpose

Use the read-only vCenter MCP connector to audit client VM resource allocations from vCenter tags and generate local billing-review artifacts.

## Required Boundaries

- Do not print or commit vCenter credentials, `.env` contents, or local config values.
- Use local runtime config under `~/.codex/vcenter-mcp/`.
- Keep vCenter actions read-only.
- Keep MCP stdout reserved for protocol traffic; write diagnostics to stderr or external files.
- Generated billing workbooks belong in `reports/` and may be tracked only when the user explicitly approves sharing the audit snapshot through git.

## Billing Workbook Workflow

1. Rebuild and verify `connectors/vcenter` before live use.
2. Confirm local config exists without displaying secrets.
3. Run a read-only VM inventory scan through `connectors/vcenter/cmd/billing-report`.
4. Use VM tags where `Client=<client name>` to group rows.
5. Include only VMs tagged `BillingScope=Billable`.
6. Create local report files in `reports/`.
7. Put Client Name in the first column and group VMs with the same Client tag together.
8. For each VM row, include CPU, MEM GB, total STORAGE GB, MECHANICAL STORAGE GB, SSD STORAGE GB, and UNKNOWN STORAGE GB.
9. STORAGE must be the total provisioned virtual disk capacity for the VM, including all attached virtual disks. Tiered storage is derived from each disk backing datastore name and must preserve unmatched datastore names in the unknown bucket.
10. Add client subtotals and workbook totals so recurring invoices can be audited and adjusted.

## Billing Workbook Decisions

- Scope: billable VMs only.
- Month: infer the current month from today's date when the user asks to run the skill, state the inferred month, and ask for confirmation before generating files.
- CLI behavior: the underlying generator should require `-month YYYY-MM`; the skill supplies it after confirmation.
- Filenames: overwrite `reports/vcenter-billing-audit-YYYY-MM.xlsx` and `reports/vcenter-billing-audit-YYYY-MM.json`.
- Sheets: `Summary`, `Billable VMs`, and `Client Mapping`.
- `Billable VMs` columns only: `Client Name`, `VM Name`, `CPU`, `MEM GB`, `STORAGE GB`, `MECHANICAL STORAGE GB`, `SSD STORAGE GB`, `UNKNOWN STORAGE GB`.
- `Summary` columns: `Client Name`, `VM Count`, `CPU Total`, `MEM GB Total`, `STORAGE GB Total`, `MECHANICAL STORAGE GB Total`, `SSD STORAGE GB Total`, `UNKNOWN STORAGE GB Total`.
- Add a subtotal row after each client group in `Billable VMs`.
- Add a grand total row across all billable clients.
- `Client Mapping` rows should be auto-populated from distinct vCenter `Client` tags.
- `Client Mapping` columns: `vCenter Client Tag`, `Normalized Match Key`, `HaloPSA Client Name`, `HaloPSA Client ID`, `Match Status`, `Notes`.
- Do not put the normalized match key in the main `Billable VMs` sheet.
- Write a JSON sidecar for later HaloPSA recurring-service reconciliation.
- Implementation path: use the repo-local Go command at `connectors/vcenter/cmd/billing-report`; it reuses existing config, inventory, tag, and report logic.

## Run Command

For the full monthly vCenter-to-HaloPSA hosting audit, prefer the repo-root command:

```bash
make hosting-audit
```

It infers the billing month from today's local date and runs the vCenter report as one step in the full audit.

After confirming the inferred month with the user, run from `connectors/vcenter`:

```bash
go run ./cmd/billing-report -config ~/.codex/vcenter-mcp/config.json -month YYYY-MM
```

or:

```bash
make billing-report MONTH=YYYY-MM
```

Report only the generated file paths and aggregate counts. Do not paste the full VM inventory unless explicitly requested.
