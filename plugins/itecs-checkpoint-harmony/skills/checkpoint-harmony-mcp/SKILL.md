---
name: checkpoint-harmony-mcp
description: Use when querying Check Point Harmony through the installed ITECS plugin for client inventory, usage or operational evidence.
---

# Check Point Harmony operations

Use the installed tools directly; no developer checkout or Go installation is needed.

- `checkpoint_harmony.profile.get`
- `checkpoint_harmony.servers.list`
- `checkpoint_harmony.tenants.list`
- `checkpoint_harmony.usage_report.get`

Usage is the monthly Portal/MSSP surface. The packaged source report also accepts an explicit Manage Accounts All Accounts ZIP/CSV export through -accounts-export when tenant inventory is needed.

Use the supplied client, period and identifiers. Resolve discoverable details with the lookup tools and ask only for missing information needed to complete the request. Use the requested month, or state the current-month assumption for an unspecified monthly report and proceed.

For Excel/JSON output, use ITECS Billing Audit: `scripts/run-source-report checkpoint-harmony -month YYYY-MM -json-only=false -out-dir /absolute/output/path`. Existing source CLI flags remain available.

Configuration lives at `~/.codex/checkpoint-harmony-mcp/config.json`; `CHECKPOINT_HARMONY_MCP_CONFIG` overrides it. Keep credential values out of output. `scripts/doctor` provides optional startup diagnostics.
