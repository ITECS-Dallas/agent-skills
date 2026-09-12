# Linux Codex support agent

Run Codex CLI under the Linux account that owns the support session, using its ChatGPT subscription login and the existing ITECS HaloPSA plugin. The server's canonical synchronized documentation is `/home/itecs/US1`. The plugin provides the existing Go connector over local stdio; it needs no OpenAI API key, separate API application server, or duplicate HaloPSA connector.

## Install the package and authenticate

Use a Linux x64 or ARM64 host with Codex CLI, Git, Bash, `curl`, and the managed prompt-free `op-itecs` wrapper. The wrapper must have access to the exact technician's Automation Vault item. Python 3 is needed only for the optional package doctor. The bundled connector requires no Go toolchain on the host.

Run setup and Codex as the same Linux account, here `itecs`, so the ChatGPT login, plugin registration, HaloPSA config and wrapper access belong to the account that executes support work. ChatGPT authentication and HaloPSA authentication are separate: subscription login runs Codex; the existing HaloPSA OAuth identity attributes ticket work to the configured technician.

Place the tested `agent-skills` checkout containing this Linux package at `$HOME/agent-skills`. The commands below install from that local marketplace. A GitHub marketplace install should use a published revision containing the Linux package; an unreleased local change is not available from `main` merely because these instructions exist.

```bash
codex login --device-auth
codex login status
codex plugin marketplace add "$HOME/agent-skills"
codex plugin add itecs-halopsa@itecs-agent-skills
codex plugin list
```

Complete the device sign-in using the intended ChatGPT subscription account and confirm `codex login status` reports ChatGPT authentication. This is the documented headless-host login method; see [Codex authentication](https://learn.chatgpt.com/docs/auth). The marketplace setup follows [OpenAI's marketplace documentation](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli); the `plugin add` syntax was checked against Codex CLI 0.153.4 help.

Configure the existing HaloPSA identity from the package directory:

```bash
cd "$HOME/agent-skills/plugins/itecs-halopsa"
./scripts/configure-halopsa-mcp-linux.sh --technician "Exact Technician Name"
```

Setup resolves `op-itecs` on `PATH`; supply `--op-command /absolute/path/to/op-itecs` if necessary. It validates the same six Automation Vault fields, technician identity, URLs, scopes and OAuth response as the macOS setup and writes command references to `~/.codex/halopsa-mcp/config.json`. Use `--config /absolute/path/to/config.json` to choose another location and set `HALOPSA_MCP_CONFIG` to that path when running Codex. Existing configurations remain valid; `--force` intentionally replaces one after setup validation succeeds. Do not copy resolved credentials into the package or a prompt.

For optional local diagnostics and tool discovery:

```bash
./scripts/doctor --discover
```

Discovery should expose 34 tools, including `halopsa.agents.me`, metadata, ticket/actions, email and status operations. Discovery alone does not prove HaloPSA authentication; in a new Codex session, request `halopsa.agents.me` and read the intended ticket to verify runtime access and identity.

## Start or resume support work

Start a new Codex session after plugin installation or refresh:

```bash
codex -C /home/itecs/US1
```

The US1 workspace supplies client documentation and local instructions. Search it for the relevant client and procedure; do not create a second documentation tree inside the plugin or substitute a workstation DOCBOT copy for the synchronized server path.

A technician can request ordinary HaloPSA lookups, notes, time logging, assignment or Start Work using the existing runtime skill. Client troubleshooting is optional. Example technician request, with the actual ticket number substituted:

> Offer the client on ticket TICKET_ID a choice of guided troubleshooting or a technician. If they opt in, use the relevant client procedure and continue on this ticket. Close it only after they clearly confirm the current issue is resolved; otherwise leave it open and hand it back with the work summary.

Use [service-desk-client-troubleshooting](../skills/service-desk-client-troubleshooting/SKILL.md) for that workflow. The technician's request authorizes the conversation and its confirmed-resolution closure once. The client chooses whether to troubleshoot. Subsequent replies reuse the authorization, inspect current ticket actions and use the existing email outcome. The agent records the fix and client confirmation, resolves a tenant-allowed closure status, and reads back the final ticket before reporting closure.

A failed diagnostic can lead to the next applicable documented step while the client wants help and the agent can perform the work. Hand off when the client declines or requests a technician, the procedure or capabilities are exhausted, or the unresolved issue calls for escalation. Ambiguity or no reply keeps the ticket open; “Thanks” and quoted older messages do not establish current resolution. The skill does not create a mailbox listener, recurring job or unattended service. Resume the authorized Codex task to inspect new ticket replies and continue from the latest exchange. If starting a separate task, include the technician's requested scope again; ticket history carries progress, not independent permission to send messages.

For a noninteractive read-only briefing from the synchronized workspace, `codex exec` can run outside a Git repository:

```bash
codex -C /home/itecs/US1 exec --skip-git-repo-check \
  'Use the HaloPSA handoff skill to summarize my current open tickets and their next actions.'
```

Do not infer continuing execution from that command returning successfully. It completes one Codex run; running again or resuming a session is an operator action unless separate scheduling was requested.

## Update and verify

After placing the updated package in the configured local marketplace, run `codex plugin add itecs-halopsa@itecs-agent-skills` and start a new Codex session. Existing sessions retain their loaded tool schema and skills.

Package implementation belongs in `GO-MCP/connectors/halopsa`; Linux binaries, setup, launcher and operator skills belong in `agent-skills/plugins/itecs-halopsa`. Local configs and ChatGPT login state remain external to both repositories. Cross-compilation, package discovery and scenario tests establish package behavior; a successful host login, representative HaloPSA read and authorized ticket conversation are separate live verification results.
