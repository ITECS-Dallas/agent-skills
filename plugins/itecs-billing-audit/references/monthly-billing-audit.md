# Monthly Billing Audit Runbook

## Purpose

Pull the current HaloPSA recurring-invoice baseline and selected read-only source-system usage, then publish one consolidated reconciliation workbook for month-end billing review. The workflow recommends and blocks actions; it does not update HaloPSA.

Run during the last week of the current month so approved corrections can be made before invoices are created on the first day of the following month.

## Primary Command

Run from the repository root:

```bash
make billing-audit
```

The local month is the default. Pin a month when repeatability matters:

```bash
MONTH=YYYY-MM make billing-audit
```

Validate orchestration without API calls or writes:

```bash
DRY_RUN=1 MONTH=YYYY-MM make billing-audit
```

Select a narrower source set:

```bash
SOURCES=vcenter,pax8 MONTH=YYYY-MM make billing-audit
```

Supported source names are `vcenter`, `pax8`, `sophos`, `checkpoint`, and `veeam`; the default is all five. HaloPSA is always required as the billing baseline. The current mapping-review/finalization authority is specifically vCenter-to-HaloPSA, so `vcenter` must be selected for `mapping-review`, `finalize`, or `full`. A non-vCenter-only selection is collect-only.

For Check Point portal-export enrichment as a collect-only source run:

```bash
CHECKPOINT_ACCOUNTS_EXPORT=~/Downloads/All\ Accounts.zip SOURCES=checkpoint MONTH=YYYY-MM make billing-audit-collect
```

For a finalizable Check Point comparison, use `SOURCES=vcenter,checkpoint` through all phases and keep the export setting on collection.

Source connectors write JSON by default. Add diagnostic workbooks only when needed:

```bash
SOURCE_WORKBOOKS=1 make billing-audit
```

Use staged execution when mapping review may require operator input:

```bash
SOURCES=vcenter,pax8 MONTH=YYYY-MM make billing-audit-collect
SOURCES=vcenter,pax8 SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID MONTH=YYYY-MM make billing-audit-mapping-review
SOURCES=vcenter,pax8 SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID MONTH=YYYY-MM make billing-audit-finalize
```

Collection generates and prints `SOURCE_RUN_ID` when it is omitted; record it and choose a new valid `RECONCILIATION_ID` for review. Reuse both exact values and the same `SOURCES` selection for finalization.

A fresh live rerun for the same month must use a new source ID; the existing source run is retained and cannot be overwritten. To recompute against unchanged source evidence, keep the source ID and use a new reconciliation ID.

Use the same explicit source list in every phase. `make billing-audit` runs `full`, which composes collection, review, and finalization for a review-clean run.

## Prerequisites

- `~/.codex/halopsa-mcp/config.json` exists.
- A local read-only connector config exists for every selected source:
  - `~/.codex/vcenter-mcp/config.json`
  - `~/.codex/pax8-mcp/config.json`
  - `~/.codex/sophos-central-mcp/config.json`
  - `~/.codex/checkpoint-harmony-mcp/config.json`
  - `~/.codex/veeam-cloud-connect-mcp/config.json`
- Secrets remain outside the repository and are resolved at runtime.
- `reports/billing-client-crosswalk.json` is a reviewed `billing-client-crosswalk-v2` revision.
- Client and service mappings have been reviewed before their rows are trusted for billing recommendations.
- Internal systems such as vCenter and Veeam are reachable through the expected private network path.

If the durable crosswalk has not been initialized, use the bounded `migrate-client-mapping` procedure in `workflows/billing-reconciliation/README.md` once. It accepts only a validated v2 mapping, refuses to overwrite an existing crosswalk, and performs no vendor call.

## Execution Contract

The script treats source collection and reconciliation as separate revisions:

- `SOURCE_RUN_ID` identifies one immutable set of vendor source artifacts.
- `RECONCILIATION_ID` identifies one offline mapping/reconciliation attempt against those exact source bytes.

The script:

1. Validates `MONTH`, `SOURCE_RUN_ID`, `RECONCILIATION_ID`, and the selected-source list.
2. Creates the IDs required by `full`; `collect` creates a source ID, while standalone review and finalization require both IDs explicitly.
3. Acquires `reports/.billing-audit.lock`; another audit targeting the same report directory must finish before this one starts.
4. `collect` pulls HaloPSA first and atomically produces `halopsa-recurring-invoices-v3` plus `halopsa-client-snapshot-v1`; it then pulls only the selected read-only source connectors. vCenter receives the same source ID.
5. It validates and exact-byte seals the selected source bundle under `reports/runs/<month>/<source_run_id>/sources/`.
6. `mapping-review` creates `reports/runs/<month>/<source_run_id>/reconciliations/<reconciliation_id>/`, freezes the durable crosswalk and service mapping, and derives a run-scoped resolution without calling any vendor API.
7. `finalize` revalidates the sealed/frozen bytes, writes the attempt-local reports and reconciliation manifest, then promotes an explicit canonical allowlist.
8. It publishes `billing-run-manifest-YYYY-MM.json` last as the canonical pointer to the certified source run and reconciliation attempt, then releases the lock.

Only `collect` and the collection portion of `full` call vendor APIs. `mapping-review` and `finalize` are offline. If review requires a crosswalk revision, keep the source run and create another reconciliation attempt instead of recollecting unchanged evidence. If only a valid disappearance confirmation is required, add it to the existing attempt and finalize with the same IDs.

Extraction, validation, ordinary publication failures, and handled `INT`/`TERM` interruptions retain or restore the prior published set. The retained staging path is printed for diagnosis. An uncatchable process kill, host crash, power loss, or filesystem failure during per-file promotion remains a residual risk; without the final success message and a valid canonical run manifest, treat the report set as incomplete and rerun or verify the manifest hashes and both IDs before use.

## Source And Mapping Authority

- HaloPSA is the canonical client, recurring-invoice, line-item, quantity, and price evidence source.
- The HaloPSA connector emits source facts only. Its correlated source contracts are `halopsa-recurring-invoices-v3` and `halopsa-client-snapshot-v1`; it does not preserve operator mappings.
- Each connector owns read-only extraction and source-quality evidence for its system.
- `workflows/billing-reconciliation` alone owns cross-system comparisons and recommendations.
- `billing-client-crosswalk-v2` is the durable, revisioned mapping and vCenter-hosting target-exclusion authority. The run-scoped `billing-client-resolution-v2` binds its exact bytes to the source run and attempt. A v2 HaloPSA client mapping is only a migration input or a derived downstream read model.
- A target exclusion must identify a stable positive HaloPSA client ID, use exact scope `vcenter-hosting`, and carry its approving crosswalk revision, UTC review timestamp, provenance, and reason. It cannot overlap a mapped HaloPSA client. It keeps the sealed HaloPSA source complete and suppresses the client only from vCenter-hosting coverage, deltas, actions, and report rows.
- Only active/source-present clients and billing-eligible HaloPSA lines participate in billed quantities.
- Only explicit `Mapped` client and service mappings can produce quantity recommendations. Suggested or pending matches remain review-only.
- Stable IDs are authoritative. A name similarity must not transfer an approved mapping to a different client.
- For vCenter, source identifiers are exact case-sensitive client tags. Normalized name matches are suggestions only.

## Reconciliation Semantics

- The comparison includes the union of delivered source facts and eligible HaloPSA charges. Missing charges and potentially orphaned/overcharged lines are both visible.
- Zero Halo target lines means `Add Missing Line` or mapping review.
- One target line means an exact update can be identified.
- Multiple target lines mean ambiguity/duplicate review, even when aggregate billed quantity matches.
- Action rows preserve exact HaloPSA recurring-invoice and line lineage.
- Estimated monthly impact is reported only when one unambiguous line has a known unit price and usable ISO currency evidence; impact values always carry that currency.
- Exact one-line quantity matches remain in the detailed reconciliation as `no_change` evidence and stay out of the action queue.
- Unknown vCenter storage blocks all storage recommendations for the affected client.
- A decrease or zero recommendation is not automatically approved; it is an evidence-backed action requiring operator review.
- A previously approved exact vCenter tag missing from the current sealed inventory requires an absence confirmation bound to the same source run, reconciliation ID, tag, and HaloPSA client ID before zero or decrease can be inferred.
- Adding, changing, or removing a target exclusion requires a new durable crosswalk revision and a new reconciliation attempt against the same sealed source run. It must not suppress another selected source's reconciliation evidence.
- vCenter includes only stable, non-template VMs explicitly tagged `BillingScope=Billable` with exactly one client tag. Stable untagged VMs are excluded: names containing `replica` case-insensitively, including `_replicate`, are Veeam replica exclusions; other untagged VMs are untagged exclusions. One exact case-sensitive `BillingScope=ITECS ASSET NO BILLING` value is excluded. Multiple, contradictory, or unrecognized scope evidence blocks the source.

## Expected Outputs

Immutable source evidence and revisioned attempts remain under:

```text
reports/runs/<month>/<source_run_id>/sources/
reports/runs/<month>/<source_run_id>/reconciliations/<reconciliation_id>/
```

Every selected connector contributes its source JSON artifact. Successful finalization publishes:

```text
reports/billing-source-manifest-YYYY-MM.json
reports/billing-client-resolution-YYYY-MM.json
reports/billing-source-facts-YYYY-MM.json
reports/billing-reconciliation-YYYY-MM.json
reports/billing-reconciliation-YYYY-MM.xlsx
reports/billing-run-manifest-YYYY-MM.json
```

Durable operator mapping inputs remain separate:

```text
reports/billing-client-crosswalk.json
reports/billing-service-line-mapping.json
reports/pax8-service-line-mapping.json
```

Finalization does not overwrite the durable mappings. `billing-run-manifest-YYYY-MM.json` is promoted last and is the canonical certification pointer. The consolidated workbook's compact `Adjustments` worksheet is the primary human action queue; detailed sheets preserve the supporting mappings and exact HaloPSA lineage. Published artifacts are owner read/write (`600`). Generated reports contain customer billing data and are ignored by default.

## Operator Review

1. Confirm the command completed and the published run manifest names the expected month, `source_run_id`, and `reconciliation_id`.
2. Review `Source Status`; each selected source must be loaded and ready, while unselected sources must say `Not Selected`.
3. Resolve source-quality and contract blockers and review source disposition counts before using deltas. For vCenter, inspect the excluded-VM ledger as well.
4. Review the run-scoped client resolution, including approved target exclusions, plus `Client Mapping Review` and `Service Mapping Review`.
5. Review the compact `Adjustments` worksheet for missing-target, duplicate/ambiguous, and exact update actions.
6. Validate each proposed adjustment against invoice ID, line ID, item identity, billed quantity, and price evidence in the detailed sheets.
7. Independently verify material decreases and estimated monthly impact.
8. Apply approved changes in HaloPSA outside this workflow and rerun the same source selection for verification.

The audit is complete only when every selected source is ready and each variance has a documented disposition. A successfully written workbook alone is not completion.

## Offline Reconciliation

Resume against a sealed source run through the operator targets. These commands do not call vendor APIs:

```bash
SOURCES=vcenter,pax8 SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID MONTH=YYYY-MM make billing-audit-mapping-review
SOURCES=vcenter,pax8 SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID MONTH=YYYY-MM make billing-audit-finalize
```

Use the exact selected-source set recorded in the source manifest. Mapping review copies the current durable crosswalk and service mapping into the attempt. If an exact mapping must change, update the durable crosswalk with a new revision and create a new `RECONCILIATION_ID` against the same source run; never edit the frozen crosswalk in an existing attempt.

If a prior approved vCenter tag is absent, verify the absence against the sealed inventory and add a same-attempt confirmation to `billing-client-resolution.json` before finalizing. The confirmation must carry the exact `vcenter_client_tag`, `halopsa_client_id`, `source_run_id`, `reconciliation_id`, UTC `confirmed_at`, review provenance, and nonblank notes. Keep multiple confirmations sorted by exact vCenter tag. Do not reuse a confirmation for another run or attempt.

## Known Operational Conditions

- The workflow is read-only and never changes HaloPSA.
- Sophos may return `Report Not Found` before the current monthly usage report is published; rerun near month end rather than substituting stale usage.
- Check Point profile lookup may not enumerate child tenants; use the documented `All Accounts` export as supplemental identity evidence.
- Pax8 invoice and draft-invoice rows remain evidence unless the source contract explicitly promotes them as quantity authority. Draft data must not drive final billing quantities.
- Network timeouts for private vCenter or Veeam endpoints are failed-source runs, not zero usage.
- On any failed run, diagnose the retained staging artifacts and rerun. Do not manually publish an incomplete subset.
- Existing audit lock: inspect `reports/.billing-audit.lock/owner` and verify that no billing audit process is still active before removing the lock; the workflow verifies ownership on release and never guesses that a lock is stale.

## Installed command package

The ITECS Billing Audit plugin bundles the existing source report commands and offline reconciler. It uses this same orchestration script with `BILLING_AUDIT_BIN_DIR` set to the absolute directory containing the native `halopsa-billing-report`, `vcenter-billing-report`, `pax8-billing-report`, `sophos-central-billing-report`, `checkpoint-harmony-billing-report`, `veeam-cloud-connect-billing-report`, and `billing-reconcile` executables (`.exe` on Windows). The plugin supplies the platform directory automatically.

When this variable is unset, source checkouts retain their existing `GO_BIN` / `go run` behavior. Both paths accept the same phases, config paths, source selection, mapping inputs, output paths and command arguments. The plugin also bundles standalone Commvault extraction; Commvault is not a selected source in the consolidated workflow.
