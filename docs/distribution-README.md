# ITECS agent-skills marketplace

This lightweight catalog installs ITECS plugins in Codex and Claude Code without cloning vendor executables or their history. Runtime executables are downloaded from immutable GitHub releases, verified against packaged SHA-256 values, and cached per user and version. Local credential configs remain under `~/.codex/<connector>-mcp/config.json` in both hosts.

Windows requires Git for Windows; Unix requires Git and Bash. The launcher uses Git's own shell on Windows and does not select WSL from PATH. No plugin-cache edits are required.

Add this catalog repository with your host's normal marketplace command, then install the plugin ID you need. The catalog identity remains `itecs-agent-skills`. Existing users must switch their old marketplace source to this repository after the organization's reviewed cutover; keep saved settings, plugin IDs and external credential configs intact.

Before first use or offline work, run from the installed plugin directory:

```text
python scripts/doctor.py --prepare
python scripts/doctor.py --discover
```

Python is needed only for these optional diagnostics. Windows can use `py -3 -X utf8` instead. Preparation downloads public runtime assets without vendor calls or credentials. The connector's approved command-backed credential setup is still required; see its plugin README. Use only `op-itecs` for managed Automation Vault access. No credential is distributed here.

MCP startup reserves stdout for protocol traffic. The doctor reports missing configs or auth environment variables without credential values. N-able's hosted MCP requires the appropriate SSO-linked API token in `ITECS_NCENTRAL_API_TOKEN`; it is separate from the direct N-central REST plugin and its existing identity.

This repository is a generated distribution. Source, development instructions and review history remain in the ITECS Agent Skills source repository.
