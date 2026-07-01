---
name: halopsa-mcp
description: Use when working on the GO-MCP HaloPSA connector, HaloPSA clients, recurring invoices, invoice line items, client mapping, billing reconciliation, or vCenter-to-HaloPSA audit workbooks.
---

# HaloPSA MCP

## Purpose

Use the read-only HaloPSA MCP connector to update the local HaloPSA client mapping source of truth and generate recurring-invoice billing artifacts for reconciliation against vCenter resource allocation reports.

## Required Boundaries

- Do not print or commit HaloPSA credentials, local config JSON, tokens, client secrets, or generated report contents.
- Use local runtime config under `~/.codex/halopsa-mcp/`.
- Standard technician setup uses 1Password CLI command-backed secrets from item `GO-MCP HaloPSA Read Only`; do not create or depend on local secret-bearing `.env` files.
- Keep HaloPSA actions read-only.
- Keep MCP stdout reserved for protocol traffic; write diagnostics to stderr or external files.
- Generated billing workbooks and JSON sidecars belong in `reports/` and may be tracked only when the user explicitly approves sharing the audit snapshot through git.

## Billing Workbook Workflow

1. Rebuild and verify `connectors/halopsa` before live use.
2. Confirm local config exists without displaying secrets and that any `op read` checks redirect output to `/dev/null`.
3. Infer the current billing month from today's date, state the inferred month, and ask for confirmation before generating files.
4. Run a read-only HaloPSA recurring-invoice scan through `connectors/halopsa/cmd/billing-report`.
5. Request recurring invoices with line items included.
6. Update `reports/halopsa-client-mapping.json` from the current HaloPSA client list.
7. Preserve manual mapping fields in the client mapping file, including canonical names, vCenter tags, Pax8 company IDs, Sophos tenant/account/external IDs, aliases, match status, and notes.
8. Create local report files in `reports/`.
9. Report only generated paths and aggregate counts unless the user explicitly asks for detail.

## Billing Workbook Decisions

- Month: infer from today's date when the user asks to run the skill, then confirm before generating files.
- CLI behavior: the underlying generator requires `-month YYYY-MM`; the skill supplies it after confirmation.
- Filenames: overwrite `reports/halopsa-recurring-invoices-YYYY-MM.xlsx` and `reports/halopsa-recurring-invoices-YYYY-MM.json`.
- Client mapping source of truth: `reports/halopsa-client-mapping.json`.
- Sheets: `Summary`, `Recurring Invoices`, `Recurring Invoice Lines`, `Client Summary`, and `Client Mapping`.
- `Recurring Invoices` should show one row per configured recurring invoice with client, invoice, contract, dates, status, and invoice-level totals.
- `Recurring Invoice Lines` should clearly show every line item on each recurring invoice, including item ID, item code, item name, description, quantity, unit price, net amount, tax amount, total price, currency, and invoice status.
- `Client Summary` should total recurring invoices and recurring invoice lines by HaloPSA client.
- `Client Mapping` should be auto-populated from HaloPSA clients and include normalized match keys for matching vCenter client tags, Pax8 company IDs, Sophos tenant/account/external IDs, and other systems.
- The workbook and JSON sidecar are meant to be cross-referenced with the vCenter billing audit workbook so an agent can identify where HaloPSA recurring invoice quantities need adjustment.

## Run Command

For the full monthly vCenter-to-HaloPSA hosting audit, prefer the repo-root command:

```bash
make hosting-audit
```

It infers the billing month from today's local date and runs the HaloPSA report as one step in the full audit.

After confirming the inferred month with the user, run from `connectors/halopsa`:

```bash
go run ./cmd/billing-report -config ~/.codex/halopsa-mcp/config.json -month YYYY-MM
```

or:

```bash
make billing-report MONTH=YYYY-MM
```

Report only generated file paths and aggregate counts. Do not paste client lists, invoice rows, invoice line items, or mapping file contents unless explicitly requested.

## Windows Runtime Notes

When validating packaged plugins on Windows, `bash` must resolve to Git Bash/MSYS/Cygwin, not WSL. If startup reports `/usr/bin/env: 'bash\r': No such file or directory`, treat it as a launcher line-ending or wrong-Bash-runtime issue before investigating HaloPSA API auth.
