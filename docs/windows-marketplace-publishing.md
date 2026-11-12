# Windows launch and lightweight marketplace publishing

Updated: 2026-11-12. Applies to Codex and Claude Code.

All nine stdio connectors dispatch their existing launcher through Git's own shell. On Windows this is Git for Windows, so a System32 WSL `bash.exe` earlier on PATH is never selected. No local plugin-cache edits, PATH changes or new runtime dependency are required. The original working directory, argument boundaries, stdin/stdout and exit status are preserved. Git for Windows remains required on Windows; Unix uses `/bin/bash`.

## Verified failures and corrections

- The published `45c6517` manifests selected bare `bash`. The former smoke test prepended Git Bash to PATH and missed the WSL failure. The replacement native test puts a failing `bash` first on PATH and checks both hosts' exact manifest invocations for every stdio connector.
- This workstation's source checkout is about 1.5 GiB. Codex CLI 0.146.1 runs a plain `git clone`, without a shallow or partial-clone flag; a fresh-add probe exceeded 55 seconds. Deleting files or publishing an orphan branch in the same repository does not remove binary history from that clone.
- Identical binary copies under `plugins/` and `claude/plugins/` share Git blob storage, but both expand during checkout. They double disk/checkout work, not the identical blob's history size.
- N-central's Claude manifest contains `Bearer ${ITECS_NCENTRAL_API_TOKEN}`, not a fixed token. An absent host variable can leave an invalid header. N-able currently documents API-token authentication; removing the header does not establish OAuth support. The package doctor reports missing variable names without values or network calls.

## Lightweight publication

Build the reviewable catalog and deterministic compressed assets:

```powershell
python scripts/build-distribution.py --output C:/staging/itecs-marketplace-release --release-url https://github.com/ITECS-Dallas/agent-skills/releases/download/REVIEWED-IMMUTABLE-TAG
```

The output contains `catalog/`, `assets/`, `RELEASE-ASSETS.json` and `DISTRIBUTION.json`. Nothing is published by this command. Every input executable must match its existing source build manifest before compression. A catalog has no vendor executables; it carries each executable's size/SHA-256 and the compressed asset's size/SHA-256 in `RUNTIME.tsv`. Codex and Claude retain their existing marketplace name, plugin IDs, skills and external config paths.

Only tracked source files enter the catalog, so an ignored local `.env` or scratch file cannot be copied into publication. When seeding the new repository from Windows, stage the catalog and restore the executable index bits from the emitted `EXECUTABLES.txt` before committing:

```powershell
git -C C:/staging/itecs-marketplace-release/catalog init -b codex/distribution-review
git -C C:/staging/itecs-marketplace-release/catalog add .
Get-Content C:/staging/itecs-marketplace-release/EXECUTABLES.txt | git -C C:/staging/itecs-marketplace-release/catalog update-index --chmod=+x --stdin
```

Publish `catalog/` to a **new repository with no binary history**. Upload every listed asset to its exact immutable GitHub release URL before announcing the catalog. The repository and assets must be readable without workstation GitHub credentials. Do not reuse a release tag for changed bytes. The new catalog requires a coordinated one-time source switch; the old source repository is retained. Do not force-push or rewrite the existing main branch to evade clone timeouts.

Existing users should switch marketplace sources only after the owner publishes and verifies the new repository. Preserve installed plugin IDs, saved host settings and `~/.codex/<connector>-mcp/config.json`; test the switch in an isolated host profile first. A PR alone does not change existing users' configured marketplace URL or publish release assets. The publishing owner must approve the organization-owned destination and perform the production cutover after review.

## Runtime preparation and offline use

A source/development package explicitly declares `runtime-mode=bundled`. A thin release explicitly declares `runtime-mode=release` and has no bundled executable fallback. It downloads only a requested platform binary, checks compressed and executable checksums, and atomically caches it under the user's `.codex/itecs-runtime/<plugin>/<version>/`. An unchanged cached version performs no network download or overwrite, including while another host uses it. Failed downloads, wrong checksums and malformed metadata fail closed.

Before first use, especially on a slow connection or before going offline, run from the installed plugin directory:

```powershell
python scripts/doctor.py --prepare
python scripts/doctor.py --discover
```

Preparation downloads public runtime assets only: no vendor API calls or credential reads. Credentials must still be configured separately using the approved managed wrapper. Windows users can use `py -3 -X utf8` instead of `python`. A cold first connection depends on asset-download time; prewarming removes that work from the host's MCP startup deadline. A missing config is reported by the doctor before starting the connector.

Billing `mapping-review`, `finalize` and direct reconciliation stay offline: a missing executable produces an instruction to prepare it, instead of attempting a download. Source collection and billing decisions are unchanged.

## Review gates

- Native Windows 11: all nine connectors, both host definitions, a wrong `bash` first on PATH, spaces/Unicode, exact tool catalogs, stdin/exit forwarding, and actual Claude CLI health check.
- macOS: all nine connectors with the same invocation tests. Linux: the shipped HaloPSA and N-central REST targets; other connectors do not publish Linux binaries. Both also run existing HaloPSA setup regressions and generated-copy parity.
- Thin catalog: cold/warm execution, compressed and native checksum failures, missing platform metadata, failed downloads, concurrent preparation, and offline refusal.
- Publication: a plain clone and isolated Codex marketplace add/upgrade against a fresh small repository; production URLs are not considered fixed until that cutover is complete.

The review-only [lightweight catalog](https://github.com/dfaria-itecs/itecs-marketplace-review-20261112/tree/codex/distribution-review) passed actual Codex CLI 0.146.1 commands in an isolated Windows 11 profile: fresh marketplace add in 6.60 seconds, upgrade in 6.78 seconds. The generated catalog is about 1.5 MiB with 72 separately sealed compressed native assets. These are workstation measurements, not a network performance guarantee. Review asset URLs are not published, so this repository is not an operational replacement marketplace.

References: [Git shell aliases](https://git-scm.com/docs/git-config#Documentation/git-config.txt-alias), [Claude MCP environment variables](https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcpjson), [N-able authentication](https://developer.n-able.com/gql/docs/mcp), [Codex marketplace configuration](https://developers.openai.com/plugins/build/plugins).
