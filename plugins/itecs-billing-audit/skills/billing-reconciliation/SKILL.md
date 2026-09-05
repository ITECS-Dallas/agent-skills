---
name: billing-reconciliation
description: Use when producing monthly source reports, reviewing billing mappings, or reconciling hosting and vendor usage against HaloPSA with the installed ITECS Billing Audit package.
---

# Billing reports and reconciliation

This plugin contains native source report commands for HaloPSA, vCenter, Pax8, Sophos Central, Check Point Harmony, Veeam Cloud Connect and Commvault, plus the offline reconciler and staged audit script. No Go installation or GO-MCP checkout is needed. Locate this installed plugin directory from the available skill path and execute its scripts by absolute path.

Use the requested month. If unspecified, state the current-month assumption and proceed. Resolve required paths and facts from the current task before asking for missing inputs. Default generated reports to a `reports` directory in the user's working folder; use an explicit output path when supplied.

## Source reports

Run `scripts/run-source-report CONNECTOR -month YYYY-MM -out-dir /absolute/output/path`. Connector names are `halopsa`, `vcenter`, `pax8`, `sophos-central`, `checkpoint-harmony`, `veeam-cloud-connect` and `commvault`. JSON is the default; add `-json-only=false` when the user wants Excel. All original source command flags are forwarded, including config, mapping and diagnostic options. Use `scripts/run-source-report CONNECTOR -h` to inspect them.

The existing per-user connector config is used by default. Config and credential values stay outside this plugin. Source extraction reports facts from one system; cross-system comparison belongs to reconciliation.

## Staged hosting and monthly audits

`run-hosting-audit` selects vCenter. `run-billing-audit` accepts `SOURCES=vcenter,pax8,sophos,checkpoint,veeam` or `all`. Set `MONTH`, `REPORTS_DIR`, `CLIENT_CROSSWALK`, and `SERVICE_LINE_MAPPING` to the intended audit and existing operator inputs.

- `AUDIT_PHASE=collect`: collect the selected vendor evidence and seal one `SOURCE_RUN_ID`.
- `AUDIT_PHASE=mapping-review SOURCE_RUN_ID=... RECONCILIATION_ID=...`: freeze the mapping revision and review identities offline.
- `AUDIT_PHASE=finalize SOURCE_RUN_ID=... RECONCILIATION_ID=...`: generate and publish the reconciliation from the same sealed evidence offline.
- `AUDIT_PHASE=full`: compose those phases when the existing mappings resolve the run.

A mapping correction creates a new reconciliation attempt against the existing source bytes; it does not require another vendor collection. Current finalization includes vCenter because the identity-resolution contract is vCenter-to-HaloPSA. Non-vCenter-only selections support collection. Commvault has a standalone report command but is not a consolidated selected source.

Read [the source workflow contract](../../references/source-billing-reconciliation.md) when resolving mappings, interpreting source quality, or reviewing decreases. The packaged scripts implement the existing source contracts and decisions. The copied [monthly runbook](../../references/monthly-billing-audit.md) explains the hosting and multi-source phases; replace repo `make` commands with the packaged scripts described here.

For direct offline diagnostics use `scripts/run-reconcile` with the original reconciler flags. Report the generated paths, source/reconciliation IDs, meaningful differences and unresolved evidence. A successful extraction is distinct from a completed reconciliation.
