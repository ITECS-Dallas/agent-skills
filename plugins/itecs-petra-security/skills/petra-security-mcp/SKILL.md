---
name: petra-security-mcp
description: Use when looking up which clients are on Petra Security (Microsoft 365 ITDR), how many licenses each is billed for, Petra tenant status, or Petra billable users through the installed ITECS Petra Security plugin.
---

# Petra Security

## Purpose

Audit Petra Security clients and license counts for billing.

## Rules

- Every tool is read-only. Never ask Petra to change anything.
- Never print, store or repeat the API key; it is read from the Automation Vault by the configured command.
- Report aggregate counts unless the user asks for client detail. Use `include_users` only when the user needs the names of billable users.
- Map a client to HaloPSA only by `microsoft_tenant_id` with an approved mapping, never by name.

## Workflow

1. For "which clients and how many licenses", call `petra.license_audit.get`. It uses the current month by default; pass `month` (YYYY-MM) for a past month.
2. Use each row's `billable_quantity`, Petra's prorated billable users. A row that is not billed has quantity 0 and an `exclusion_reason`: `paused`, `trial`, `not_for_resale` or `deleted`.
3. Check `source_quality.status`. Only `Ready` supports a billing decision. If it is `Blocked`, report the listed issues instead of totals.
4. Report `caveats`, such as disabled accounts that still hold a license, or tenants paused since a past month.
5. For one client's current users, call `petra.billable_users.get` with its `petra_tenant_id`.
   - It returns counts, including disabled accounts.
   - Petra allows about one such call a minute, and the tool waits automatically.
   - `user_evidence` on the audit does this for every billed client.

## Setup issues

- **Config not found:** a missing config means `~/.codex/petra-security-mcp/config.json` does not exist yet. Point the user to the plugin README.
- **HTTP 401:** the API key was revoked or the Vault item name is wrong. A Petra Admin can create a new key.
