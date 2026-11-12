# Windows marketplace validation

Updated: 2026-11-12. Review branch: `codex/halopsa-windows11-validation`.

The launch fix bypasses WSL through Git's own shell. All nine shipped Windows/macOS stdio connectors passed both host-manifest invocations. Lightweight publication is staged and measured; production remains on the existing source until review and a coordinated catalog/asset publication.

## Fixes and evidence

| Area | Result |
| --- | --- |
| Windows shell selection | Replaced bare `bash` in all nine stdio manifests. Tests place a failing bash first on PATH and preserve nested working directory, literal arguments, stdin/stdout and exit status. |
| HaloPSA source | Windows home-path expansion, credential-command error redaction, native file-attribute tests and portable test scripts are in [GO-MCP PR 26](https://github.com/ITECS-Dallas/GO-MCP/pull/26). |
| Marketplace size | A tracked-files-only builder emits a roughly 1.5 MiB catalog and 72 deterministic compressed assets, with compressed/native hashes and native sizes. It never publishes or rewrites history. |
| Release cache | Explicit bundled/release modes, atomic installation, checksum rejection, concurrent preparation, offline refusal and prewarming. Fixed a macOS Bash 3.2 exit-trap scope bug found by native CI. |
| N-central HTTP | Manifest uses an environment reference, not a fixed token. Doctor now identifies the required missing variable without exposing its value or contacting N-able. Authentication was not exercised. |
| Diagnostics | Doctor checks external config before discovery and can prepare runtime assets without accessing vendor APIs or credentials. |

## Native test matrix

Runtime/package revision tested by the full matrix: `ac03e5b128027d02a07d546b89f8f3a93a191284`.

| Environment | Coverage | Result |
| --- | --- | --- |
| Windows 11, build 26300, amd64 | Nine stdio connectors through Codex and Claude manifests; synthetic configs; wrong bash first; spaces/Unicode; transport forwarding; HaloPSA Windows PowerShell 5.1 setup | Passed |
| Windows 11, Claude Code CLI 2.1.321 | Real `mcp add-json` / `mcp list` health check against HaloPSA in an isolated profile | Connected; no vendor request |
| Native Windows CI | All nine connectors, both manifests, cold/warm/corrupt/concurrent/offline cache, publication boundaries, Windows PowerShell setup | Passed |
| macOS 15, arm64 CI | All nine connectors, both manifests, same cache/publication tests, existing macOS/Linux setup and launcher regressions | Passed |
| Ubuntu CI | HaloPSA and N-central REST published Linux targets, cache/publication tests and HaloPSA setup regressions; other plugins explicitly report no shipped Linux target | Passed |
| Windows 11, Codex CLI 0.146.1 | Fresh lightweight marketplace add, upgrade and HaloPSA plugin installation in an isolated `CODEX_HOME` | Passed: 6.60 s, 6.78 s and 1.11 s respectively |

Full native package matrix: [CI run 43295892123](https://github.com/ITECS-Dallas/GO-MCP/actions/runs/43295892123). The private repository workflow checks out the exact public review commit because public-fork Windows/macOS runner availability was delayed. [HaloPSA source tests and native builds](https://github.com/ITECS-Dallas/GO-MCP/actions/runs/43277974944) also passed. Existing tests were retained.

## Limits and remaining publication work

- These tests use synthetic credentials and loopback endpoints. They verify startup, protocol/tool catalogs, setup, transport and packaging; they do not certify live HaloPSA/N-able credentials or vendor API operations.
- A later local Windows 11 HTTPS fixture run rejected the ephemeral test CA with Schannel. The complete fixture passes native Windows CI. Public GitHub asset downloads are not verified because the planned immutable assets are not published. No test changes Windows trust stores or disables certificate verification.
- The [review catalog](https://github.com/dfaria-itecs/itecs-marketplace-review-20261112/tree/codex/distribution-review) is public, binary-free and explicitly marked review-only. Its successful clone timings are measurements on this workstation, not a performance guarantee. Do not point production hosts at it.
- Before rollout, publish all sealed assets and an organization-owned catalog in a fresh repository without binary history, then validate real downloads and migrate marketplace sources in an isolated host profile before announcing the switch. The existing repository and main history remain intact. The [publishing runbook](../windows-marketplace-publishing.md) contains the procedure.
- [Marketplace PR 33](https://github.com/ITECS-Dallas/agent-skills/pull/33) and source PR 26 remain open for requester/Brian review. Nothing was merged to main. The original workspace's unrelated changes were left untouched.
