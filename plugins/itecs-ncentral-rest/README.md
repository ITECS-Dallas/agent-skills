# N-central Direct REST MCP

Read-only access to a self-hosted N-central server using the official REST API and official MCP Go SDK. The connector never changes SSO providers, users, roles, devices or scripts. Each technician uses a User-API JWT from their existing N-central account; an Entra/SSO account does not need a duplicate local identity. REST token authentication is separate from interactive Entra SSO.

## Tools

- `ncentral_rest.servers.list`: configured servers; no credentials or network access.
- `ncentral_rest.org_units.list`: one page of organizations, including customers and sites.
- `ncentral_rest.customers.list`: all visible customers after complete organization pagination.
- `ncentral_rest.devices.list`: one page of devices, including `isProbe`.
- `ncentral_rest.devices.get`: exact device ID and its current inventory fields.
- `ncentral_rest.inventory.summary`: complete customer/site/device counts, with probes and non-probe devices counted separately.

The only POST route is `/api/auth/authenticate`, which exchanges a User-API JWT for a short-lived access token. All data routes are fixed GET endpoints. There is no generic HTTP, script, remote-control, mutation or write-mode tool. Redirects are rejected. Auth tokens are kept in memory per configured server. Expired access tokens are re-exchanged; one data HTTP 401 permits one reauthentication, while 403, 429 and server errors are surfaced without retries. Source warnings, malformed records, inconsistent counts, duplicate IDs and changed pagination totals fail closed. Collections are live reads, not atomic snapshots or billing artifacts.

## Configure

Store non-secret runtime configuration at `~/.codex/ncentral-mcp/config.json`. Copy `config.example.json`, set the server's HTTPS origin, and use a credential command with an absolute executable path. On the authorized ITECS macOS host, the command is:

```json
["/opt/homebrew/bin/op-itecs", "read", "op://Automation Vault/N-central REST - YOUR IDENTITY/credential"]
```

The reference is an example. Store the technician's existing User-API JWT in a concealed `credential` field in an approved Automation Vault item. API tokens are generated from the existing user's API Access tab. Never store an Entra password, JWT or access token in config, source, `.env`, shell arguments, reports or chat. Stop on an `op-itecs` failure; do not use alternate credential sources. Other hosts require their approved absolute wrapper executable path. For Windows JSON, forward slashes avoid backslash escaping. The plugin uses bundled native binaries, so technicians do not need Go.

A valid token proves authentication, not complete fleet coverage. API results are limited to the source user's roles and access groups. Keep individual technician identity and scope; do not distribute another technician's token. The connector enforces read-only routes even when a token's account has broader permissions.

## Install from marketplace

```bash
codex plugin marketplace upgrade itecs-agent-skills
codex plugin add itecs-ncentral-rest@itecs-agent-skills
```

Start a new chat after installation. This plugin uses `ncentral_rest`; the separately available `itecs-ncentral` plugin uses the official hosted GraphQL MCP and has different identity prerequisites. Neither path is an automatic fallback for the other. Do not enable the hosted plugin for a direct-REST setup unless it is independently configured and needed.

## Build and validate

From this connector directory:

```bash
go test -race ./...
go vet ./...
make build
```

Live verification is opt-in: list servers, run the inventory summary, list customers, then read one known device and compare its exact ID/name/customer with the console. Compare the console's Network Devices count with `non_probe_devices`; `device_records` also includes probes. Check the user's expected customer scope. Never interpret missing access as an empty fleet.

## References

- [Official REST authentication](https://developer.n-able.com/n-central/docs/managing-authentication)
- [Official REST quickstart and server-local API explorer](https://developer.n-able.com/n-central/docs/quickstart)
