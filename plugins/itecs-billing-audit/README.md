# ITECS Billing Audit

Run the existing GO-MCP report and reconciliation commands without installing Go or a source checkout. Supports macOS Apple Silicon/Intel and Windows ARM64/x64 with Git Bash. Config and reports remain outside the plugin.

## Standalone Excel/JSON reports

From your working folder, set the installed plugin path and run its scripts:

```bash
BILLING_PLUGIN="/absolute/path/to/installed/itecs-billing-audit"
"$BILLING_PLUGIN/scripts/run-source-report" vcenter -month 2026-09 -json-only=false -out-dir "$PWD/reports"
"$BILLING_PLUGIN/scripts/run-source-report" halopsa -month 2026-09 -json-only=false -out-dir "$PWD/reports"
"$BILLING_PLUGIN/scripts/run-source-report" veeam-cloud-connect -month 2026-09 -json-only=false -out-dir "$PWD/reports"
```

The same command accepts `pax8`, `sophos-central`, `checkpoint-harmony`, and `commvault`. Defaults are the current month, `./reports`, and the existing per-user connector config. All original report flags pass through. For Pax8 and Sophos the default is standalone extraction with no client mapping prefill; pass `-client-mapping` for an existing derived mapping when needed. Use `CONNECTOR -h` for command help.

## Staged hosting audit

Supply your existing operator mapping files. They are not bundled with the public plugin. Use an output directory outside the plugin cache so upgrades preserve the audit evidence.

```bash
export MONTH=2026-09
export REPORTS_DIR="/absolute/path/to/audit/reports"
export CLIENT_CROSSWALK="/absolute/path/to/billing-client-crosswalk.json"
export SERVICE_LINE_MAPPING="/absolute/path/to/billing-service-line-mapping.json"
AUDIT_PHASE=collect "$BILLING_PLUGIN/scripts/run-hosting-audit"
SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID AUDIT_PHASE=mapping-review "$BILLING_PLUGIN/scripts/run-hosting-audit"
SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID AUDIT_PHASE=finalize "$BILLING_PLUGIN/scripts/run-hosting-audit"
```

Use the source ID printed by collection. For selected multiple sources use `SOURCES=vcenter,pax8,sophos,checkpoint,veeam ./scripts/run-billing-audit`. The existing `DRY_RUN=1` option prints commands without vendor calls. `SOURCE_WORKBOOKS=1` adds diagnostic source workbooks.

All existing audit environment options remain supported, including per-connector `HALOPSA_CONFIG`, `VCENTER_CONFIG`, `PAX8_CONFIG`, `SOPHOS_CONFIG`, `CHECKPOINT_CONFIG`, `VEEAM_CONFIG` and the mapping/output paths. The launcher also understands the connector plugins' `*_MCP_CONFIG` overrides. Windows defaults use USERPROFILE.

Only collection calls vendor APIs. Current mapping review and finalization require vCenter in the selected source set. Commvault is available as standalone extraction. `scripts/run-reconcile` exposes the original offline diagnostic modes.

## Reference and diagnostics

See `skills/billing-reconciliation/SKILL.md` and the copied source runbooks under `references/`. `BUILD-MANIFEST.json` records source revision, binary hashes and copied resource hashes. Optional `scripts/doctor` requires Python 3 and reports package details without reading config values.
