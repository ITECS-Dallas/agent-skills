# ITECS N-central Plugin

`itecs-ncentral` connects Codex directly to the **official N-able hosted MCP service** at `https://api.n-able.com/mcp-read-only`. It uses Codex's native HTTP transport and bearer-token environment support; no Go binary, Node bridge, or community REST MCP server is bundled.

## Self-hosted N-central

N-able states that its MCP service supports on-premises N-central customers. This is a connection through N-able's cloud GraphQL platform, not a direct connection to your server's REST API. Your N-able SSO account must expose the intended server and customers. A local N-central User-API JWT is not the token required here.

Inventory visibility for a particular server must be verified after authentication. A successful installation or MCP handshake does not establish complete customer coverage. This plugin does not add a monthly billing source or a normalized billing artifact contract to GO-MCP.

## Install

With the ITECS marketplace already configured:

```bash
codex plugin add itecs-ncentral@itecs-agent-skills
```

Install the option only on machines that need it. Use the global marketplace; do not add duplicate project MCP definitions. Start a new chat after installation.

## Authentication

Create an API token at [N-able API Token Management](https://n-able.app/api-token-management), using the N-able SSO identity whose customer access is intended. Tokens inherit that identity's permissions. Store the token in the approved 1Password Automation Vault through the authorized vault workflow. No token or vault item is provisioned by this package.

The plugin reads `ITECS_NCENTRAL_API_TOKEN` from the **Codex host process environment**. Keep token values out of plugin/config files, shell profiles, command arguments, logs and chat. Do not use secret-bearing `.env` files. For example, on the authorized ITECS macOS host, after storing the token in the example item/field below, launch Codex CLI in a subshell:

```bash
(
  set +x
  ITECS_NCENTRAL_API_TOKEN="$(/opt/homebrew/bin/op-itecs read 'op://Automation Vault/N-able MCP/api_token')" || exit 1
  test -n "$ITECS_NCENTRAL_API_TOKEN" || exit 1
  export ITECS_NCENTRAL_API_TOKEN
  codex
)
```

`N-able MCP/api_token` is an example item/field reference, not a claim that it exists. Use the approved reference for your identity. Stop on any `op-itecs` failure; do not substitute plain `op`, another vault or a plaintext token. Other hosts need their approved absolute wrapper path.

A terminal export does not update an already-running desktop app. Desktop use requires supplying the variable to its host through an approved environment mechanism before launch; this package does not install a persistent credential injector. Installation remains available without credentials, but live tools require this setup. Do not assume OAuth login is supported solely because the client offers it; follow N-able's current authentication documentation.

## Verify access

1. Confirm the N-central MCP tools are visible and inspect their current schemas.
2. Use schema discovery/validation and a small read to retrieve customers and device counts.
3. Compare the returned customers and device counts with the self-hosted N-central console under equivalent permissions.
4. Read one known device's details and metrics to verify identity and freshness.

Treat missing customers, null fields, pagination and partial results explicitly. Never interpret an inaccessible or incomplete inventory as zero devices. Record live verification separately from package validation.

The read-only URL is fixed in this package. Do not switch to `/mcp` or `/mcp-preview` to fix an error: those endpoints permit production changes. This option is for inventory, troubleshooting and reporting.

## References

- [Official N-able MCP setup, endpoints and authentication](https://developer.n-able.com/gql/docs/mcp)
- [N-able on-premises availability announcement](https://status.n-able.com/2026/04/14/introducing-the-public-preview-of-n-zo-n-ables-ai-assistant-and-the-n-able-mcp-server/)
- [Current N-able MCP capabilities](https://developer.n-able.com/gql/docs/mcp-capabilities)
- [Codex HTTP MCP configuration](https://learn.chatgpt.com/docs/extend/mcp#streamable-http-servers)
