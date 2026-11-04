---
name: pax8-mcp
description: Use when looking up live Pax8 companies, subscriptions, licenses, products, invoices, vendor-service billing facts, or Pax8-to-HaloPSA billing evidence through the ITECS read-only Pax8 MCP plugin.
---

# Pax8 MCP

## Purpose

Use the bundled read-only Pax8 MCP server for live Pax8 lookup workflows in Codex. This plugin is appropriate for company lookup, subscription and license review, product lookup, invoice evidence, draft invoice item evidence, vendor-service billing facts, and Pax8-to-HaloPSA reconciliation support.

## Required Boundaries

- Standardize repo names and paths as `pax8`, even if the prompt says "PACS 8".
- Do not print or commit Pax8 credentials, local config JSON, tokens, raw exports, generated report contents, or sensitive customer detail unless the user explicitly asks for the detail.
- Use local runtime config under `~/.codex/pax8-mcp/`.
- Standard technician setup uses 1Password CLI command-backed secrets from item `GO-MCP Pax8 Read Only`; do not create or depend on local secret-bearing `.env` files.
- Keep Pax8 actions read-only.
- Keep MCP stdout reserved for protocol traffic.
- Summarize results by default; provide row-level details only when the user requests them.

## Operating Pattern

1. Confirm the user's goal and the minimum Pax8 data needed.
2. Use narrow filters before broad list calls.
3. Start with company or subscription lookup before requesting invoice or invoice-item detail.
4. Treat draft invoice items as pre-final evidence; do not use them as billing truth without explicit review context.
5. Preserve evidence fields in the answer: Pax8 IDs, company/customer names, subscription/product identifiers, quantities, statuses, dates, and match rationale.
6. Report uncertainty plainly when a lookup is inconclusive.

## Local Setup

Each machine needs local config outside the plugin:

```text
~/.codex/pax8-mcp/config.json
```

The config should call `op read` for the approved 1Password item fields, normally:

```text
op://ITECS/GO-MCP Pax8 Read Only/PAX8_CLIENT_ID
op://ITECS/GO-MCP Pax8 Read Only/PAX8_CLIENT_SECRET
```

The plugin launcher also honors:

```bash
PAX8_MCP_CONFIG=/absolute/path/to/config.json
```

Never store credentials in this plugin repository.

## Windows Startup Troubleshooting

If Pax8 tools are not callable, check startup layers before checking vendor auth:

1. Confirm the plugin is installed and the Codex thread was started after install.
2. On Windows, confirm `bash -lc 'uname -s'` returns `MINGW`, `MSYS`, or `CYGWIN`; WSL Bash is not supported.
3. Treat `/usr/bin/env: 'bash\r': No such file or directory` as a launcher line-ending or wrong-Bash-runtime issue, not a Pax8 API issue.
4. Treat `codex.exe` under `WindowsApps` returning `Access is denied` as a local Codex/PATH issue.
5. Confirm `op --version`, `op account list`, and `op read ... >/dev/null` work without printing secret values.
