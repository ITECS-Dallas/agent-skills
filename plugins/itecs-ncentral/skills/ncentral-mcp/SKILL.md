---
name: ncentral-mcp
description: Use when querying N-central device inventory, customer coverage, device details, health metrics or reporting through the ITECS plugin for the official N-able read-only MCP service.
---

# N-central MCP

Use the installed `ncentral` server backed by the official N-able GraphQL MCP service. The plugin fixes the endpoint to `https://api.n-able.com/mcp-read-only`. It supports self-hosted N-central through the N-able platform; it does not call a local N-central REST endpoint directly.

- Inspect the advertised tools and schemas before relying on tool names or fields. Use `search`, `introspect`, `validate` and `execute` when advertised, or available dedicated read tools.
- Resolve the exact customer and device identity before retrieving details. Use narrow queries and honor pagination, result limits and partial errors.
- Authentication inherits the API token creator's N-able SSO permissions. Missing customers or null fields can reflect access restrictions. Do not report zero devices or complete fleet coverage without verifying inventory completeness.
- Preserve customer/device identifiers, source timestamps and relevant units in findings. Summarize by default; disclose only the customer detail needed for the request.
- Keep this integration read-only. Do not change endpoints or enable writes to overcome an authentication or capability error.
- A successful MCP handshake establishes connectivity only. Validate expected self-hosted server/customer coverage and a known device before claiming readiness.
- This plugin does not supply a GO-MCP monthly billing source contract. Keep cross-system mapping and billing reconciliation in their owning workflow.

For installation and environment-backed token setup, read [the plugin README](../../README.md). Never print or extract token values into chat. Programmatic Automation Vault reads use the approved absolute `op-itecs` wrapper; stop on wrapper failure.
