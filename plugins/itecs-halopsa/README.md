# ITECS HaloPSA for Atlas

Version 0.16.1 packages 53 typed tools (27 reads and 26 writes) for macOS, Windows and Linux, including tenant metadata, the authenticated technician, billing contracts and charge rates, edits of existing time entries, notes, clients, contacts, sites and assets, compact reads for AI sessions, change history, timesheet and asset reads, and the sales opportunity workflow: Project Opportunities, prospect clients and contacts, internal document attachments and opportunity workflow stages. The technician's request authorizes its stated actions, including client-visible, creation, stage and billing changes. All writes use `confirm`; Atlas resolves required facts internally and does not ask for repeated approval. Draft-only requests stay drafts.

See [the runtime workflow](skills/halopsa-mcp/SKILL.md) for current operation behavior and [Linux support-agent setup](docs/linux-support-agent.md) for ChatGPT subscription authentication, packaging and the canonical `/home/itecs/US1` documentation workspace. The optional [client troubleshooting and how-to skill](skills/service-desk-client-troubleshooting/SKILL.md) continues replies on an existing ticket and closes only after the client clearly confirms resolution or intended task completion. Restart into a new Codex task after updating the plugin.

## What changed in 0.16.1

On macOS, a session left open across a plugin upgrade no longer loses HaloPSA. Before this release, a session whose connector had started but not yet called HaloPSA when an upgrade landed failed every call with `tls: failed to verify certificate: SecPolicyCreateSSL error: 0` until it restarted.

That error isn't a certificate problem. The upgrade deletes the previous release's folder, and the connector could then no longer build its macOS certificate policy. The connector now prepares the macOS certificate verifier when it starts, so an open session keeps working on the version it started with until you restart it.

Certificate checks are unchanged, and all 53 tools work as they did in 0.16.0.

Sessions already running 0.16.0 or earlier don't have the fix. Install 0.16.1 with the same commands as 0.16.0 below, then restart open sessions.

If a session still reports `SecPolicyCreateSSL error: 0`, restart that session. Once a session runs the new release, `halopsa.servers.list` with `include_status: true` reports `connector_version` 0.16.1.

## What changed in 0.16.0

- Asset updates preserve existing asset-type values, including during notes-only and inactive-only changes. A partial field edit replaces only that field's value; duplicate metadata rows cannot hide stored values.
- Contract `description` now writes the writable HaloPSA `note` field. Contract creation and updates include independent field-by-field readback; the computed `refextra` reference is no longer used as a description.
- Shared readback reports omitted values and nested mismatches instead of claiming success. Ticket and project text, dates and budgets now receive automatic readback too.
- Scope reporting and setup documentation use the working `read:sales` and `edit:sales` scopes. Keep `edit:customers`, `edit:assets` and `edit:contracts` on each technician's existing application and Vault scope when those write tools are needed. Credentials remain outside the plugin.

All 53 tools remain available. The release passed the connector tests, race tests, vet, package checks and live regressions on the designated test records, with the original values restored.

For a Git-backed marketplace, run `codex plugin marketplace upgrade itecs-agent-skills`, then `codex plugin add itecs-halopsa@itecs-agent-skills`. For a local-path marketplace, first run `git pull --ff-only` in its clean `agent-skills` checkout, then the same plugin-add command. Start a new session to load the release, and use `halopsa.servers.list` with `include_status: true` to verify version 0.16.0 and configured scope coverage.

## What changed in 0.15.0

- **Correct time entries and notes.** `halopsa.ticket_actions.update` edits an existing action: hours, non-billable hours, billing type by name (`charge_rate`) or id, contract by reference or id, date done, note, private or public, important, travel, mileage and reviewed. HaloPSA recalculates the entry's billing when it is saved, so moving an entry to a billable rate on a pre-pay contract deducts its hours and moving it back releases them. Correct the entry instead of logging a second one. `halopsa.ticket_actions.delete` removes one action and confirms it is gone.
- **Edit customers and assets.** `halopsa.clients.update`, `halopsa.users.update` and `halopsa.sites.update` edit clients, contacts and sites (site address lines merge into the current address, and no email is sent). `halopsa.assets.create` and `halopsa.assets.update` create and edit assets, setting asset-type fields such as a hostname or serial number by id or name.
- **Any other field.** The edit tools and `halopsa.tickets.update`, `halopsa.projects.update` and `halopsa.contracts.update` accept `extra_fields`, a map of other HaloPSA fields by API name sent as given. Tickets, projects, clients, contacts, sites and assets also take `custom_fields` by id.
- Every edit previews against the record's current values, writes once and reads the record back. No new refusals were added.

Scopes: action edits and deletes need `edit:tickets`. Client, contact and site updates need `edit:customers`, and asset writes need `edit:assets`; `halopsa.servers.list` with `include_status: true` shows which ones the configured scope covers.

## What changed in 0.14.0

- **Contracts on tickets and projects.** `halopsa.tickets.update`, `halopsa.projects.update` and the two create tools link a record to its billing contract by `contract_ref` (the reference, matched exactly within the record's client) or `contract_id`; the update tools also take `clear_contract`. The connector refuses another client's contract and any contract that is inactive, not started or expired. Previews show the contract being linked and the one it replaces, and the write is read back. A time entry on a record with no contract draws from nothing, so link the contract first. See [ticket-billing-readiness](skills/ticket-billing-readiness/SKILL.md).
- **Billing types by name.** `halopsa.ticket_actions.create_time_entry` takes `charge_rate` by name (`No Charge` is sent explicitly); the preview shows the resolved rate, the ticket's contract state and warnings, and the entry is read back. `halopsa.metadata.list` kind `charge_rates` returns named billing types with effective hourly rates (it used to return unnamed rate rows); `contract_subtypes`, `billing_descriptions` and `lookup` read other HaloPSA pick-lists. Contract reads add `subtype_label` and `billing_description_label`.
- **Compact reads.** `compact: true` on ticket, project, contract, client, action and metadata reads returns the working fields without the duplicated raw payload (a detailed ticket drops by about 95%). `halopsa.agents.me` no longer returns the agent's 2 MB language pack unless `include_full` is set. Other defaults that changed: contract reads add the label fields, the `charge_rates` catalog returns named rates, and a ticket or project update that sets an id field or contract reads the record back once. No existing field was removed or renamed.
- **Context tools.** `halopsa.tickets.audit` (who changed a field and when), `halopsa.time_entries.list` (an agent's logged time for a date window, with charge types and totals), `halopsa.assets.list` and `halopsa.assets.get`. `halopsa.tickets.list` accepts `contract_id` and `include_time_taken`; `halopsa.ticket_actions.list` accepts `time_entries_only`.
- **Self-diagnosis.** `halopsa.servers.list` with `include_status: true` reports the connector version, the authenticated agent, the configured OAuth scopes and which tool groups they cover, so a missing scope is explained before a write fails. `check_updates: true` also says whether a newer plugin release exists.
- **Safer closure and rate limits.** `halopsa.tickets.update_status` accepts the `expected_last_update` from a ticket read, so a new client reply stops an automatic closure even when the status is unchanged. Reads that HaloPSA rate-limits wait for its `Retry-After`.

Scopes: linking a contract and logging time need `edit:tickets`. Creating or editing contract records needs `edit:contracts`, `halopsa.time_entries.list` needs `read:timesheets`, and `halopsa.assets.*` need `read:assets`. Add them to the item's `HALO_SCOPE` and the HaloPSA API application's permissions only where that technician needs them.

## Tool Surface

The bundled MCP server exposes the current GO-MCP HaloPSA tools:

- `halopsa.servers.list`
- `halopsa.metadata.list`
- `halopsa.agents.me`
- `halopsa.clients.list`
- `halopsa.clients.get`
- `halopsa.invoices.list`
- `halopsa.invoices.get`
- `halopsa.recurring_invoices.list`
- `halopsa.recurring_invoices.get`
- `halopsa.contracts.list`
- `halopsa.contracts.get`
- `halopsa.contracts.create`
- `halopsa.contracts.update`
- `halopsa.purchase_orders.list`
- `halopsa.purchase_orders.get`
- `halopsa.projects.list`
- `halopsa.projects.get`
- `halopsa.projects.create`
- `halopsa.projects.update`
- `halopsa.projects.update_status`
- `halopsa.tickets.list`
- `halopsa.tickets.get`
- `halopsa.ticket_statuses.list`
- `halopsa.ticket_actions.list`
- `halopsa.ticket_outcomes.list`
- `halopsa.ticket_outcomes.get`
- `halopsa.ticket_actions.start_work`
- `halopsa.ticket_actions.send_email`
- `halopsa.ticket_actions.create_public_note`
- `halopsa.ticket_actions.create_private_note`
- `halopsa.ticket_actions.create_time_entry`
- `halopsa.tickets.create`
- `halopsa.tickets.update`
- `halopsa.tickets.update_status`
- `halopsa.opportunities.list`
- `halopsa.opportunities.create`
- `halopsa.opportunities.update`
- `halopsa.opportunities.execute_workflow_action`
- `halopsa.clients.create`
- `halopsa.users.create`
- `halopsa.attachments.list`
- `halopsa.attachments.upload`
- `halopsa.tickets.audit`
- `halopsa.time_entries.list`
- `halopsa.assets.list`
- `halopsa.assets.get`
- `halopsa.ticket_actions.update`
- `halopsa.ticket_actions.delete`
- `halopsa.clients.update`
- `halopsa.users.update`
- `halopsa.sites.update`
- `halopsa.assets.create`
- `halopsa.assets.update`

Ticket action reads support conversation/public filters, date windows and optional email HTML. Keep `agent_only` false to include client replies, and preserve action IDs/authorship when continuing a conversation.

Technicians can request a ticket or project in ordinary chat. The agent resolves supplied names to HaloPSA IDs and asks concise follow-up questions only when required values remain missing; technicians do not compose tool payloads. Ticket and project creation require at least one category ID plus positive HaloPSA impact and urgency values. Opportunities use `halopsa.opportunities.create` instead, which needs no support classification and enforces the opportunity type's own mandatory fields.

## Sales opportunity workflow

The [sales opportunity workflow skill](skills/sales-opportunity-workflow/SKILL.md) records a new inquiry and its updates without the browser: prospect client (`halopsa.clients.create`), contact (`halopsa.users.create`), Project Opportunity (`halopsa.opportunities.create`), internal sales notes, cheat sheets, the approved SOW and approval evidence (`halopsa.attachments.upload`), and workflow stages (`halopsa.opportunities.execute_workflow_action`).

- Previews come from live tenant reads: the opportunity type's mandatory fields and choices, the workflow's current step and transition, and field-group members. They report `ready_to_execute`, `missing` and `warnings`.
- Duplicates are refused: an existing client name (ignoring case, punctuation, spacing and legal suffixes), an existing contact email, or an open opportunity with the same summary for the client.
- Each write is attempted once and followed by the connector's own field-by-field `readback`. Report completion from that readback; never retry a mismatch or error.
- Attachments are internal, limited to documents, spreadsheets, presentations, saved email and images up to 20 MiB, and refused for hidden paths. Upload requires the SHA-256 shown in the preview.
- Workflow actions are limited to an opportunity's current workflow step, are recorded as private actions without email or time, and refuse HaloPSA system actions such as creating a child project.
- `halopsa.tickets.list` does not return opportunities; use `halopsa.opportunities.list`.

All write tools use `confirm`: omitted or false for preview, true for an action the technician has requested. That request also covers its client-visible, creation/status and billing steps; no additional category-based confirmation is required. Previews can resolve fields without creating a user approval stage. Ask only for missing required information or an unresolved material choice. Snapshot/status revalidation and independent readback remain part of execution; reconcile ambiguous writes before retrying. Prefer typed tools when suitable, and use other available authorized routes for missing operations. Follow the workspace's authoritative workflow and sender routing, including graph-mail for Brian where configured.

When a technician authorizes the optional client support conversation, that authorization covers its invitation, relevant replies, progress notes and closure after the client's clear confirmation of resolution or how-to completion. Do not request repeated technician confirmation for those actions. Offer only for a clearly simple problem or desired task with a known standard-user approach, then wait for client acceptance before giving steps. Examples include the user's own editable signature, out-of-office setup and ordinary bookmark export/import. Judge the impact as well as required privileges: destructive data/profile resets, security/sharing/sync/forwarding/mailbox-rule changes and identity recovery remain technician work. Never assume the POC has administrative access or company authorization. ATLAS is preferred but not mandatory for well-understood general technical guidance. A failed step can lead to another applicable simple user-level step. Decline, a request for a technician, exhausted suitable steps/capabilities, administrative work or an unresolved issue requiring escalation lead to a handoff; unresolved issues and no response leave the ticket open. Handoff does not itself page, reassign or change priority. This is an on-demand Codex workflow using the existing tools; it does not install a background agent or poller. The separately deployed RELAY worker admits only eligible new client email support tickets; the connector's broader tools do not expand that scope.

`Start Work` resolves exactly one currently available tenant outcome named `Start Work` and posts that outcome through `/Actions`; it never substitutes a generic status update. Outcome metadata can disclose configured status, assignment, workflow, email, billing, and timer effects. Halo's continuously running browser timer is UI state, so the connector does not claim that it remains open. Explicit time logging is supported through `halopsa.ticket_actions.create_time_entry`.

Ticket email uses one exact email-capable configured outcome and `confirm: true` for the authorized execution. It does not write directly to Halo's outgoing-email queue.

For additional agents, the assigned queue, co-managed workflows or change-request
plans, use `halopsa.tickets.get` with its normal detailed response. Read
`ticket_context.assignment`, `workflow`, `change_management` and `custom_fields`.
Queue means the ticket's returned `team`/`team_id`. Custom Change Plan,
Implementation Plan, Test Plan and Backout Plan values may be populated while the
native plan fields are blank; inspect both and preserve field IDs when labels
repeat. Missing fields are unavailable, not confirmed empty. Discover tenant
workflow names with metadata kind `workflows` and native/custom plan definitions
with kind `fields` and search `plan`; use kind `teams` for queue IDs.

## Runtime Configuration

Store live HaloPSA config and credentials outside this repository:

```text
~/.codex/halopsa-mcp/config.json
```

The launcher uses this config path by default:

```bash
~/.codex/halopsa-mcp/config.json
```

Override it per session with:

```bash
export HALOPSA_MCP_CONFIG=/absolute/path/to/config.json
```

Each technician uses that technician's own Automation Vault item named `GO-MCP HaloPSA <Technician> Read Write`. The setup scripts validate all six expected fields, exact agent identity, approved URLs, ticket and optional sales scopes, and OAuth before writing a config. The generated file contains only command-backed references for `HALO_CLIENT_ID`, `HALO_CLIENT_SECRET`, and `HALO_SCOPE`; it never contains resolved credentials.

Each technician must use that technician's own `GO-MCP HaloPSA <Technician> Read Write` identity so HaloPSA attribution remains individual. The credential must retain the required read permissions and `edit:tickets`; `halopsa.servers.list` with `include_status: true` shows which tool groups the configured scopes cover. The sales opportunity writes also need `read:sales` and `edit:sales` (opportunity updates, workflow actions and attachments) and `edit:customers` (client and contact creation) on both the item's `HALO_SCOPE` and the HaloPSA API application's permissions; without them HaloPSA rejects those writes. A live write test uses the technician's designated test record and authorized action with the existing preview and readback behavior.

Do not commit `.env`, local config JSON, API tokens, client secrets, raw HaloPSA exports, or generated billing reports.

### macOS Setup

Use the managed prompt-free ITECS wrapper. Do not fall back to plain `op`:

```bash
./scripts/configure-halopsa-mcp-macos.sh --technician "Exact Technician Name"
```

Use `--force` only when intentionally replacing that technician's existing local config.

### Linux Setup

Run from the installed plugin directory as the Linux account that runs Codex:

```bash
./scripts/configure-halopsa-mcp-linux.sh --technician "Exact Technician Name"
```

The script resolves the managed prompt-free `op-itecs` wrapper on `PATH`. Use `--op-command /absolute/path/to/op-itecs` when it is installed elsewhere. It shares the existing Automation Vault, identity, scope and OAuth validation with macOS, and writes command references to `~/.codex/halopsa-mcp/config.json`. See [the Linux guide](docs/linux-support-agent.md) for prerequisites, installation and Codex login.

### Windows 11 Setup

Run in PowerShell from the installed plugin directory:

```powershell
.\scripts\configure-halopsa-mcp-windows.ps1 `
  -TechnicianName "Exact Technician Name" `
  -ItecsAccount "ITECS-1PASSWORD-ACCOUNT-SHORTHAND"
```

The Windows script resolves the installed `op.exe`, validates the exact per-technician Automation Vault item and live OAuth response, and writes `%USERPROFILE%\.codex\halopsa-mcp\config.json` with command references only. If the item is absent, inaccessible, mismatched, over-scoped, or rejected by OAuth, stop for credential restoration/rotation; do not use another technician's identity or a shared fallback.

## Supported Platforms

Bundled MCP binaries are included for:

- macOS Apple Silicon: `darwin-arm64`
- macOS Intel: `darwin-amd64`
- Linux x64: `linux-amd64`
- Linux ARM64: `linux-arm64`
- Windows 11 x64: `windows-amd64.exe`
- Windows 11 ARM64: `windows-arm64.exe`

The plugin launcher is a Bash script. Windows 11 machines need Git Bash/MSYS/Cygwin Bash available as `bash` on `PATH`; it resolves the default config from `%USERPROFILE%` so PowerShell setup and Git Bash startup use the same file. WSL Bash is not supported for this launcher.

Windows preflight:

```powershell
where.exe bash
bash -c 'uname -s; uname -m'
```

The first result must begin with `MINGW`, `MSYS` or `CYGWIN`. If it is `Linux`, `bash` resolves to WSL; put Git Bash earlier on PATH and restart Codex.

For an engineering smoke test from the installed plugin directory, run:

```powershell
py -3 -X utf8 .\scripts\test-windows.py
```

Use `python -X utf8` if Python is installed without the `py` launcher. This test runs the actual Windows binary through the plugin launcher, checks all 53 tool names, and exercises default and override config paths in a temporary profile with spaces and Unicode. It uses synthetic command-backed credentials and invokes no Halo operations. It does not alter the technician's saved config or prove their live 1Password access. Python is needed for this optional engineering check, not for the Go connector itself.

If startup fails with `/usr/bin/env: 'bash\r': No such file or directory`, refresh the plugin after the launcher line-ending fix and verify Git Bash is the active `bash`. That error happens before HaloPSA authentication and should not be treated as a vendor API permission issue.

## Install From The ITECS Marketplace

For another Codex installation:

```bash
codex plugin marketplace add https://github.com/ITECS-Dallas/agent-skills.git --ref main
codex plugin add itecs-halopsa@itecs-agent-skills
```

Start a new Codex thread after installing so the plugin MCP tools are loaded.

## Refresh An Existing Installation

After this marketplace repository is updated, refresh the marketplace snapshot and reinstall the plugin so Codex replaces its cached runtime:

```bash
codex plugin marketplace upgrade itecs-agent-skills
codex plugin add itecs-halopsa@itecs-agent-skills
```

If `codex plugin marketplace list` shows `itecs-agent-skills` pointing at a folder on disk (a local clone), update that clone instead of running `marketplace upgrade`: `git -C <that folder> pull --ff-only`, then `codex plugin add itecs-halopsa@itecs-agent-skills`. A machine whose clone was never pulled keeps installing the old version.

Then restart Codex Desktop or start a new thread. Existing threads keep the tool schema that was loaded when the thread started. Windows and Linux machines run the same two commands.

Confirm the update from a new thread: ask Atlas to call `halopsa.servers.list` with `include_status: true` and `check_updates: true` and check that `connector_version` is the current plugin version and `update_available` is false. Without an AI session, `scripts/doctor --discover` lists the tools the installed binary exposes, and `scripts/doctor` prints the installed version. Your existing 1Password configuration is unchanged by an update; if the new tools report a missing scope, only the item's `HALO_SCOPE` and the API application's permissions need adjusting.

Claude Code users who launch the connector from the newest build under `~/.codex/plugins/cache/itecs-agent-skills/itecs-halopsa/` pick up the new version after the two commands above and a restart of Claude Code.

## Local Smoke Test

From this plugin directory:

```bash
bash ./scripts/run-halopsa-mcp
```

For feature discovery without printing secrets:

```bash
go run github.com/modelcontextprotocol/go-sdk/examples/client/listfeatures@latest \
  bash ./scripts/run-halopsa-mcp
```

## Source Of Truth

The connector implementation source of truth remains the sibling GO-MCP checkout:

```text
GO-MCP/connectors/halopsa
```

Rebuild this plugin's binaries only from that connector after its tests pass.

## Packaged reporting and diagnostics

ITECS Billing Audit provides source Excel/JSON reports and the staged reconciliation commands without Go or a developer checkout. Use its `scripts/run-source-report halopsa -month YYYY-MM -json-only=false -out-dir /absolute/output/path`. Ordinary lookups continue to use this plugin's bundled MCP tools.

Run `scripts/doctor` for optional local version, platform and config-presence diagnostics (Python 3). Add `--discover` to list the actual MCP tools; discovery starts the configured server and resolves its credential commands but invokes no vendor operation. Config contents and credential values are not printed. `BUILD-MANIFEST.json` records the source revision, platform binaries and SHA-256 hashes.
