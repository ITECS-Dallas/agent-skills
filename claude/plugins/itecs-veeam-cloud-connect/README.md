# ITECS Veeam Cloud Connect

Bundled Veeam Cloud Connect MCP tools for macOS Apple Silicon/Intel and Windows ARM64/x64.

## Setup

Install `itecs-veeam-cloud-connect@itecs-agent-skills` from the ITECS marketplace. Reuse the existing local config at `~/.codex/veeam-cloud-connect-mcp/config.json`, or adapt `config.example.json` to the actual server and command-backed credential item. The example contains placeholders, not an issued credential. On the ITECS Mac use `/opt/homebrew/bin/op-itecs` for 1Password commands; on Windows use the configured 1Password CLI account. Keep config outside the plugin so updates preserve it.

Windows launchers use Git Bash and resolve the user directory from USERPROFILE. Set `VEEAM_CLOUD_CONNECT_MCP_CONFIG` for another config path.

## Tools

- `veeam_cloud_connect.backup_agents.list`
- `veeam_cloud_connect.companies.list`
- `veeam_cloud_connect.license_reports.latest`
- `veeam_cloud_connect.license_usage.list`
- `veeam_cloud_connect.protected_computer_restore_points.list`
- `veeam_cloud_connect.protected_computers.list`
- `veeam_cloud_connect.servers.list`
- `veeam_cloud_connect.storage_usage.list`

## Reports and diagnostics

Install ITECS Billing Audit for packaged `scripts/run-source-report veeam-cloud-connect` and Excel/JSON output. All original report flags are supported. Run `scripts/doctor` for optional local diagnostics (Python 3); add `--discover` to list actual MCP tools without invoking a vendor operation.

## Source

Implementation remains in GO-MCP `connectors/veeam-cloud-connect`. The package build manifest records its source revision and binary hashes.
