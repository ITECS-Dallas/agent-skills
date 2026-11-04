# ITECS Sophos Central

Bundled Sophos Central MCP tools for macOS Apple Silicon/Intel and Windows ARM64/x64.

## Setup

Install `itecs-sophos-central@itecs-agent-skills` from the ITECS marketplace. Reuse the existing local config at `~/.codex/sophos-central-mcp/config.json`, or adapt `config.example.json` to the actual server and command-backed credential item. The example contains placeholders, not an issued credential. On the ITECS Mac use `/opt/homebrew/bin/op-itecs` for 1Password commands; on Windows use the configured 1Password CLI account. Keep config outside the plugin so updates preserve it.

Windows launchers use Git Bash and resolve the user directory from USERPROFILE. Set `SOPHOS_CENTRAL_MCP_CONFIG` for another config path.

## Tools

- `sophos_central.billing_usage.get`
- `sophos_central.firewall_licenses.list`
- `sophos_central.servers.list`
- `sophos_central.tenant_licenses.get`
- `sophos_central.tenants.list`
- `sophos_central.whoami.get`

## Reports and diagnostics

Install ITECS Billing Audit for packaged `scripts/run-source-report sophos-central` and Excel/JSON output. All original report flags are supported. Run `scripts/doctor` for optional local diagnostics (Python 3); add `--discover` to list actual MCP tools without invoking a vendor operation.

## Source

Implementation remains in GO-MCP `connectors/sophos-central`. The package build manifest records its source revision and binary hashes.
