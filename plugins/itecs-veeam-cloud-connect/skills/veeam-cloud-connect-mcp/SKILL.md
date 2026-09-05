---
name: veeam-cloud-connect-mcp
description: Use when querying Veeam Cloud Connect through the installed ITECS plugin for client inventory, usage or operational evidence.
---

# Veeam Cloud Connect operations

Use the installed tools directly; no developer checkout or Go installation is needed.

- `veeam_cloud_connect.backup_agents.list`
- `veeam_cloud_connect.companies.list`
- `veeam_cloud_connect.license_reports.latest`
- `veeam_cloud_connect.license_usage.list`
- `veeam_cloud_connect.protected_computer_restore_points.list`
- `veeam_cloud_connect.protected_computers.list`
- `veeam_cloud_connect.servers.list`
- `veeam_cloud_connect.storage_usage.list`

For restore-point evidence, resolve the company and protected-computer ID, then list its restore points. Preserve restore-point dates and sizes; a listed restore point is evidence of its presence, not proof of a tested restore. Storage and agent quantities have distinct company/tenant scopes.

Use the supplied client, period and identifiers. Resolve discoverable details with the lookup tools and ask only for missing information needed to complete the request. Use the requested month, or state the current-month assumption for an unspecified monthly report and proceed.

For Excel/JSON output, use ITECS Billing Audit: `scripts/run-source-report veeam-cloud-connect -month YYYY-MM -json-only=false -out-dir /absolute/output/path`. Existing source CLI flags remain available.

Configuration lives at `~/.codex/veeam-cloud-connect-mcp/config.json`; `VEEAM_CLOUD_CONNECT_MCP_CONFIG` overrides it. Keep credential values out of output. `scripts/doctor` provides optional startup diagnostics.
