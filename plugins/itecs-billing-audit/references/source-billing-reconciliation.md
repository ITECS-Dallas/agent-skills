---
name: billing-reconciliation
description: Use when working in this repo on cross-system billing audits, variance workbooks, client mapping, service-line mapping, or reconciling vCenter, HaloPSA, Pax8, Sophos, Check Point, or Veeam billing artifacts.
---

# Billing Reconciliation

## Purpose

Use the offline consolidated workflow to compare selected read-only source facts with HaloPSA recurring-invoice lines. The operator runbooks are:

- `docs/runbooks/monthly-billing-audit.md`
- `docs/runbooks/monthly-hosting-audit.md`

## Required Boundaries

- Never call live vendor APIs from `workflows/billing-reconciliation`.
- Keep extraction and source-quality evidence inside `connectors/<system>`.
- Keep all cross-system comparisons, blockers, and recommendations inside `workflows/billing-reconciliation`.
- Treat HaloPSA as the canonical billing client and invoice-line identity.
- Do not mutate HaloPSA or a source system from this workflow.
- Do not print or commit report contents, local config, credentials, or tokens.
- Keep generated artifacts under `reports/`; share a snapshot through git only with explicit user approval.

## Required Contracts

For consolidated hosting, require and validate:

- `halopsa-recurring-invoices-v3`
- `halopsa-client-snapshot-v1`
- `vcenter-billing-audit-v2` when vCenter is selected
- `billing-source-run-manifest-v1`
- `billing-client-crosswalk-v2`
- `billing-client-resolution-v2`
- `billing-service-line-mapping-v1`
- matching month and correlated `source_run_id`
- `source_quality.status: "Ready"` and `ready: true`
- nonempty vCenter included baseline, stable unique IDs, finite nonnegative quantities, count/tier invariants, and unique mappings

The source manifest must seal the exact bytes, size, source, schema, and role of every required source artifact. `source_run_id` identifies that immutable evidence set. `reconciliation_id` identifies one offline attempt using a frozen crosswalk revision and service-line mapping against that evidence. Never overwrite or reinterpret either identity.

The durable crosswalk is the only approval authority for exact vCenter-client-tag to HaloPSA-client-ID mappings and reviewed target exclusions. Normalized names may produce suggestions but may not approve identity. A v2 HaloPSA client mapping is accepted only as an explicit migration input or emitted as a run-scoped derived read model after resolution; do not restore it as a live connector output.

Each `target_exclusions` row must use a stable positive HaloPSA client ID and exact scope `vcenter-hosting`, carry the approving crosswalk revision, UTC review timestamp, provenance, and reason, and remain disjoint from mapped HaloPSA IDs. Keep the sealed HaloPSA snapshot and recurring-invoice artifact complete. Apply the exclusion only to vCenter-hosting coverage, deltas, action rows, and report rows; it must not suppress another source reconciliation. Any exclusion change requires a new crosswalk revision and a new reconciliation attempt against the sealed source run.

Validate routine vCenter exclusions against producer semantics. `itecs_asset_no_billing_excluded` requires exactly one exact case-sensitive `BillingScope=ITECS ASSET NO BILLING` value. `veeam_replica_name_excluded` requires stable identity, `template=false`, zero BillingScope tags, and a VM name containing `replica` case-insensitively. `billing_scope_untagged_excluded` requires stable identity, `template=false`, zero BillingScope tags, and a VM name that does not match the replica rule. No exclusion rule may override contradictory, multiple, or unrecognized BillingScope evidence.

Reject older or malformed hosting artifacts. Do not add a compatibility fallback.

## Monthly Workflow

1. Use `collect` to call HaloPSA and the selected source connectors, validate their source contracts, and seal an immutable source run under `reports/runs/<month>/<source_run_id>/sources/`.
2. Use `mapping-review` with the sealed `source_run_id` and a new `reconciliation_id`. It freezes the current durable crosswalk and service-line mapping into the attempt, derives exact-tag coverage and suggestions, and calls no vendor API.
3. Resolve current-tag blockers or reviewed target exclusions by revising `reports/billing-client-crosswalk.json`, then create a new reconciliation attempt against the same source run. Do not edit the frozen crosswalk inside an existing attempt.
4. When a previously approved exact vCenter tag is absent from the current sealed inventory, add an explicit absence confirmation to that attempt's `billing-client-resolution.json`. The confirmation must bind the exact tag and HaloPSA client ID to the same `source_run_id` and `reconciliation_id`; absence without confirmation cannot authorize a zero or decrease.
5. Use `finalize` only after the resolution is complete. Finalization revalidates exact input bytes, writes the attempt-local report set and reconciliation manifest, and publishes the canonical month-named files with the run manifest last. It calls no vendor API.

`full` composes the phases for a review-clean run. If it stops at mapping review, preserve the sealed source run and resume offline; do not recollect unchanged evidence merely to resolve a mapping.

## Decision Rules

- Only explicit `Mapped` client and service mappings can produce quantity recommendations.
- `Suggested`, `Pending`, `Unmapped`, inactive, stopped, source-missing, and duplicate mappings remain review-only.
- Use active/source-present HaloPSA clients and active, billing-eligible lines only.
- Reconcile the union of delivered source facts and eligible HaloPSA lines so both missing charges and potential overcharges surface.
- A zero/decrease is allowed only for an explicitly mapped active client with a complete selected-source baseline. Missing evidence is a blocker.
- An approved exact source identifier missing from the current source baseline is not zero evidence until a same-source-run, same-reconciliation absence confirmation is present.
- Preserve canonical client, recurring-invoice, line, and eligible item IDs plus exact invoice/line/item lineage, billed quantity, `unit_price_known`, unit price, currency, status, and eligibility.
- Zero eligible target lines means add/identify a target; one means an exact update; more than one means ambiguous/duplicate review even when aggregate delta is zero.
- A billing-eligible HaloPSA line may belong to only one selected source/service key.
- Keep an exact one-line quantity match as a `no_change` detail row, but exclude it from `Action Summary` and action-required totals.
- Calculate estimated monthly impact only for one exact line with known unit-price evidence and a recognized usable ISO 4217 currency; always carry the currency with the impact.

## vCenter Storage

- Use exact bytes from the v2 vCenter contract for total, mechanical, SSD, and unknown storage.
- Validate total bytes equal the sum of tier bytes at VM, client, and report levels.
- Convert to configured 50 GB billing blocks and apply ceiling rounding only at the final unit boundary.
- If a client has any unknown-tier storage, block all storage actions for that client, especially decreases.
- Do not use aggregate-only storage artifacts or a legacy `storage_gb` mapping as billing authority.

## Selected Sources

Require `-selected-sources` for consolidated execution. Supported aliases are `vcenter`, `pax8`, `sophos`, `checkpoint`, and `veeam`; `all` expands to all five. Never load unselected artifacts. Report them as `Not Selected`.

HaloPSA is always the baseline and is not part of this list.

The current staged client-resolution contract is specifically vCenter-to-HaloPSA, so `mapping-review`, `finalize`, and `full` require `vcenter` in the selected set. A selection containing only non-vCenter systems may run `collect` but must not be documented as finalizable until its own client-resolution authority is implemented.

## Commands

Full monthly audit when mapping review is expected to be clean:

```bash
make billing-audit
```

Hosting only:

```bash
make hosting-audit
```

Dry-run orchestration:

```bash
DRY_RUN=1 MONTH=YYYY-MM SOURCES=vcenter make billing-audit
```

Staged hosting workflow from the repository root:

```bash
MONTH=YYYY-MM make hosting-audit-collect
SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID MONTH=YYYY-MM make hosting-audit-mapping-review
SOURCE_RUN_ID=SOURCE_ID RECONCILIATION_ID=RECON_ID MONTH=YYYY-MM make hosting-audit-finalize
```

The equivalent multi-source targets are `billing-audit-collect`, `billing-audit-mapping-review`, and `billing-audit-finalize`; pass the same explicit `SOURCES` value to every phase. Only the collect target calls vendor APIs.

Legacy specialized offline diagnostic modes remain from `workflows/billing-reconciliation`. They are not the canonical monthly path and must receive an explicitly prepared, validated run-scoped derived v2 client mapping:

```bash
go run ./cmd/reconcile -source pax8 -month YYYY-MM -client-mapping /path/to/derived-client-mapping.json
go run ./cmd/reconcile -source halopsa-contracts -month YYYY-MM -client-mapping /path/to/derived-client-mapping.json
```

## Outputs And Review Order

Immutable source evidence and revisioned attempts live under:

```text
reports/runs/<month>/<source_run_id>/sources/
reports/runs/<month>/<source_run_id>/reconciliations/<reconciliation_id>/
```

After successful finalization, the canonical published set includes:

```text
reports/billing-source-manifest-YYYY-MM.json
reports/billing-client-resolution-YYYY-MM.json
reports/billing-source-facts-YYYY-MM.json
reports/billing-reconciliation-YYYY-MM.json
reports/billing-reconciliation-YYYY-MM.xlsx
reports/billing-run-manifest-YYYY-MM.json
```

Treat `billing-run-manifest-YYYY-MM.json`, published last, as the canonical pointer to the certified source and reconciliation IDs. The durable `reports/billing-client-crosswalk.json` is an operator input and is not replaced by finalization.

Review in this order:

1. `Source Status` for selection, readiness, and run correlation.
2. Source-quality blockers, disposition counts, and `vCenter Exclusions` when vCenter is selected.
3. The compact `Adjustments` worksheet for the human action queue.
4. `Client Mapping Review` and `Service Mapping Review` for approval and exclusion evidence.
5. Missing-target, duplicate/ambiguous, exact-line, and no-change detail rows.

Writing a workbook or obtaining a zero delta does not by itself make a row safe to apply.

## Validation

After changes, run from `workflows/billing-reconciliation`:

```bash
gofmt -w ./cmd ./internal
go test ./...
go vet ./...
```

When orchestration changes, also run from the repo root:

```bash
bash -n scripts/billing-audit.sh scripts/hosting-audit.sh
shellcheck scripts/billing-audit.sh scripts/hosting-audit.sh scripts/billing-audit_test.sh scripts/testdata/*.sh
bash scripts/billing-audit_test.sh
```
