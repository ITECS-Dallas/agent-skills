---
name: ncentral-mcp
description: Use when querying a self-hosted N-central server directly for customers, organization units, devices or inventory counts through the ITECS read-only REST plugin, without changing existing Entra SSO.
---

# N-central Direct REST

Use the `ncentral_rest` tools from `itecs-ncentral-rest`. This is an ITECS connector using the official N-central REST API, not N-able's hosted GraphQL MCP. Keep existing technician SSO identities and role/access-group scope.

- Start with `ncentral_rest.servers.list`; select the exact configured server ID.
- For complete coverage, use `inventory.summary` and `customers.list`. A single `devices.list` or `org_units.list` call is only one page. Honor page metadata when listing additional pages.
- Inventory includes probes. Compare `non_probe_devices` with the console's Network Devices view and report `probe_devices` separately. Preserve customer/device IDs and source timestamps in findings.
- Verify a known device with `devices.get` before claiming readiness. Valid authentication alone does not prove expected customer coverage. A zero or partial result can mean restricted source permissions.
- Keep all source actions read-only. Do not change SSO, create duplicate users, generate tokens, alter roles or access groups as a routine lookup step.
- Resolve credentials only through the approved absolute `op-itecs` executable. Stop on wrapper failure. Never print secrets or use plain `op`, another vault, secret-bearing config or `.env` files.
- Runtime config lives outside the plugin at `~/.codex/ncentral-mcp/config.json` (override: `NCENTRAL_MCP_CONFIG`). Configure an HTTPS origin and `jwt_command` for the technician's own existing N-central User-API JWT, stored in a concealed `credential` field. Different hosts need their approved absolute wrapper path.
- This connector exposes no mutation tools, generic HTTP, remote-control links, or billing contract. Keep cross-system billing logic in its owning workflow.

Read [the connector README](../../README.md) for configuration, endpoint behavior and installation.
