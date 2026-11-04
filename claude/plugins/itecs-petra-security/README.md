# ITECS Petra Security

Version 0.1.0 packages five read-only tools for Petra Security, the Microsoft 365 identity threat detection platform. They audit which clients are on Petra and how many licenses each is billed for, on macOS and Windows. Every call is a read; nothing in Petra is changed.

| Tool | Use |
|---|---|
| `petra.license_audit.get` | Per-client license audit for a billing month: Microsoft tenant ID, status, licensed users, billable quantity or why it is not billed (paused, trial, not for resale, deleted), totals and source quality. |
| `petra.tenants.list` | Client tenants with Petra and Microsoft tenant IDs and paused state. |
| `petra.usage.get` | Petra's usage for every tenant for the month containing `as_of`. |
| `petra.billable_users.get` | One client's current billable users, including disabled accounts that still hold a license; `include_users` adds the list. |
| `petra.servers.list` | Configured targets, without the key. |

Ask, for example: "Which clients are on Petra and how many licenses are we billed for this month?"

## Setup

1. A Petra Admin creates an API key in `app.petrasecurity.com` under Settings → API Keys and saves it in the Automation Vault.
2. Copy `config.example.json` to `~/.codex/petra-security-mcp/config.json` (`%USERPROFILE%\.codex\petra-security-mcp\config.json` on Windows), and make it owner-only.
3. Set `api_key_command` to the `op-itecs` read of that Vault item. The file holds only the command, never the key. `PETRA_SECURITY_MCP_CONFIG` overrides the path.
4. Install the plugin from the `itecs-agent-skills` marketplace and start a new session.

## Notes

- **Quantity:** the billable quantity is Petra's billable users for the month, already prorated for mid-month onboarding.
- **Join key:** each client's Microsoft tenant ID is the key for matching it to its HaloPSA client.
- **Rate limit:** Petra allows about one per-client user lookup a minute, and the tools wait automatically. A current-month audit with `user_evidence` takes about a minute per billed client.
- **Past months:** a past month is read as of its last day, and per-user evidence is available for the current month only.
- **Reconciliation:** Petra is not yet a source in the monthly billing reconciliation.

`scripts/doctor` reports the installed version and config presence; `--discover` lists the tools without calling Petra.
