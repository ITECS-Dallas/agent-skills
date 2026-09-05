---
name: commvault-mcp
description: Use when querying Commvault through the installed ITECS plugin for client inventory, usage or operational evidence.
---

# Commvault operations

Use the installed tools directly; no developer checkout or Go installation is needed.

- `commvault.accounts.list`
- `commvault.billing_snapshot.get`
- `commvault.servers.list`
- `commvault.usage_summary.get`

Accounts provide tenant/service presence. Usage Summary provides partner-level SKU quantities. Do not present partner totals as individual tenant quantities; report the scope the source actually returns.

Use the supplied client, period and identifiers. Resolve discoverable details with the lookup tools and ask only for missing information needed to complete the request. Use the requested month, or state the current-month assumption for an unspecified monthly report and proceed.

For Excel/JSON output, use ITECS Billing Audit: `scripts/run-source-report commvault -month YYYY-MM -json-only=false -out-dir /absolute/output/path`. Existing source CLI flags remain available.

Configuration lives at `~/.codex/commvault-mcp/config.json`; `COMMVAULT_MCP_CONFIG` overrides it. Keep credential values out of output. `scripts/doctor` provides optional startup diagnostics.
