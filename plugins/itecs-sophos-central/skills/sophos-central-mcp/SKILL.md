---
name: sophos-central-mcp
description: Use when querying Sophos Central through the installed ITECS plugin for client inventory, usage or operational evidence.
---

# Sophos Central operations

Use the installed tools directly; no developer checkout or Go installation is needed.

- `sophos_central.billing_usage.get`
- `sophos_central.firewall_licenses.list`
- `sophos_central.servers.list`
- `sophos_central.tenant_licenses.get`
- `sophos_central.tenants.list`
- `sophos_central.whoami.get`

Resolve tenant IDs through the tenant list. Monthly Partner billing usage and current tenant/firewall licenses answer different questions; preserve their period and units. A report-not-yet-available response is not zero usage.

Use the supplied client, period and identifiers. Resolve discoverable details with the lookup tools and ask only for missing information needed to complete the request. Use the requested month, or state the current-month assumption for an unspecified monthly report and proceed.

For Excel/JSON output, use ITECS Billing Audit: `scripts/run-source-report sophos-central -month YYYY-MM -json-only=false -out-dir /absolute/output/path`. Existing source CLI flags remain available.

Configuration lives at `~/.codex/sophos-central-mcp/config.json`; `SOPHOS_CENTRAL_MCP_CONFIG` overrides it. Keep credential values out of output. `scripts/doctor` provides optional startup diagnostics.
