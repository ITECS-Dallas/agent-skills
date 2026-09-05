# ITECS Commvault

Bundled Commvault MCP tools for macOS Apple Silicon/Intel and Windows ARM64/x64.

## Setup

Install `itecs-commvault@itecs-agent-skills` from the ITECS marketplace. Reuse the existing local config at `~/.codex/commvault-mcp/config.json`, or adapt `config.example.json` to the actual server and command-backed credential item. The example contains placeholders, not an issued credential. On the ITECS Mac use `/opt/homebrew/bin/op-itecs` for 1Password commands; on Windows use the configured 1Password CLI account. Keep config outside the plugin so updates preserve it.

Windows launchers use Git Bash and resolve the user directory from USERPROFILE. Set `COMMVAULT_MCP_CONFIG` for another config path.

## Tools

- `commvault.accounts.list`
- `commvault.billing_snapshot.get`
- `commvault.servers.list`
- `commvault.usage_summary.get`

## Reports and diagnostics

Install ITECS Billing Audit for packaged `scripts/run-source-report commvault` and Excel/JSON output. All original report flags are supported. Run `scripts/doctor` for optional local diagnostics (Python 3); add `--discover` to list actual MCP tools without invoking a vendor operation.

## Source

Implementation remains in GO-MCP `connectors/commvault`. The package build manifest records its source revision and binary hashes.
