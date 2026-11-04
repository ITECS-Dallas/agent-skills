# ITECS Check Point Harmony

Bundled Check Point Harmony MCP tools for macOS Apple Silicon/Intel and Windows ARM64/x64.

## Setup

Install `itecs-checkpoint-harmony@itecs-agent-skills` from the ITECS marketplace. Reuse the existing local config at `~/.codex/checkpoint-harmony-mcp/config.json`, or adapt `config.example.json` to the actual server and command-backed credential item. The example contains placeholders, not an issued credential. On the ITECS Mac use `/opt/homebrew/bin/op-itecs` for 1Password commands; on Windows use the configured 1Password CLI account. Keep config outside the plugin so updates preserve it.

Windows launchers use Git Bash and resolve the user directory from USERPROFILE. Set `CHECKPOINT_HARMONY_MCP_CONFIG` for another config path.

## Tools

- `checkpoint_harmony.profile.get`
- `checkpoint_harmony.servers.list`
- `checkpoint_harmony.tenants.list`
- `checkpoint_harmony.usage_report.get`

## Reports and diagnostics

Install ITECS Billing Audit for packaged `scripts/run-source-report checkpoint-harmony` and Excel/JSON output. All original report flags are supported. Run `scripts/doctor` for optional local diagnostics (Python 3); add `--discover` to list actual MCP tools without invoking a vendor operation.

## Source

Implementation remains in GO-MCP `connectors/checkpoint-harmony`. The package build manifest records its source revision and binary hashes.
