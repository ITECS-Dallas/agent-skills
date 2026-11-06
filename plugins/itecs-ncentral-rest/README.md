# N-central Direct REST MCP

Read-only access to a self-hosted N-central server using the official REST API and official MCP Go SDK. The connector never changes SSO providers, users, roles, devices or scripts. Automatic ITECS setup uses the existing Automation Vault API reader; custom per-technician User-API JWTs are also supported. Entra/SSO accounts do not need duplicate local identities. REST token authentication is separate from interactive Entra SSO.

## Tools

- `ncentral_rest.servers.list`: configured servers; no credentials or network access.
- `ncentral_rest.org_units.list`: one page of organizations, including customers and sites.
- `ncentral_rest.customers.list`: all visible customers after complete organization pagination.
- `ncentral_rest.devices.list`: one page of devices, including `isProbe`.
- `ncentral_rest.devices.get`: exact device ID and its current inventory fields.
- `ncentral_rest.inventory.summary`: complete customer/site/device counts, with probes and non-probe devices counted separately.

The only POST route is `/api/auth/authenticate`, which exchanges a User-API JWT for a short-lived access token. All data routes are fixed GET endpoints. There is no generic HTTP, script, remote-control, mutation or write-mode tool. Redirects are rejected. Auth tokens are kept in memory per configured server. Expired access tokens are re-exchanged; one data HTTP 401 permits one reauthentication, while 403, 429 and server errors are surfaced without retries. Source warnings, malformed records, inconsistent counts, duplicate IDs and changed pagination totals fail closed. Collections are live reads, not atomic snapshots or billing artifacts.

## Automatic ITECS configuration

On first start after installation, the launcher creates `~/.codex/ncentral-mcp/config.json` automatically if no configuration exists. No per-machine N-central setup command is required. The non-secret file points to `https://manage.itecsonline.com` and the existing `N-central REST - Existing API Reader` item in `Automation Vault` (`op://Automation Vault/h6b4ek24qjuqdjjrvrtagfsnme/credential`). Its permissions are owner-only on POSIX hosts. No token value is read during setup or written to disk.

Each machine must already have its approved, prompt-free `op-itecs` wrapper and a machine service account with read access to that vault item. macOS uses `/opt/homebrew/bin/op-itecs`; Windows uses `%ProgramFiles%/ITECS/Automation/op-itecs.exe`, provisioned by the N-central enrollment workflow; Linux resolves `op-itecs` on PATH. Existing custom configs are preserved. Administrators provision machine-specific service accounts and OS credential-store access through the [N-central endpoint enrollment workflow](https://github.com/ITECS-Dallas/GO-MCP/tree/codex/endpoint-vault-provisioning/workflows/endpoint-vault). The plugin itself never creates a vault grant or copies credentials between machines. A successful managed deployment leaves technicians with only the plugin installation step. Missing wrapper, denied vault access, an expired token or an API failure is reported without trying another credential source.

The default uses the shared API reader's N-central role/access-group scope; it does not impersonate the signed-in technician. Existing Entra/SSO accounts are unchanged. The connector restricts every data operation to read-only REST routes even if the API account has broader permissions.

### Custom configurations

Existing configuration files are preserved, including custom per-technician credentials and server scope. `NCENTRAL_MCP_CONFIG` selects an explicit config; a missing explicit path fails instead of creating defaults. To use a different server or a technician's own existing User-API JWT, copy `config.example.json`, set the HTTPS origin, and use an approved absolute credential command referencing the concealed `credential` field in Automation Vault. Never put JWTs, Entra passwords or access tokens in configuration, `.env`, source, logs or chat.

A valid token proves authentication, not complete fleet coverage. Compare the expected customer/device scope with the console. Do not treat missing access as an empty fleet.

## Install from marketplace

```bash
codex plugin marketplace upgrade itecs-agent-skills
codex plugin add itecs-ncentral-rest@itecs-agent-skills
```

Start a new chat after installation. The first MCP launch performs the automatic setup above. This plugin uses `ncentral_rest`; the separately available `itecs-ncentral` plugin uses the official hosted GraphQL MCP and has different identity prerequisites. Neither path is an automatic fallback for the other. Do not enable the hosted plugin for a direct-REST setup unless it is independently configured and needed.

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
