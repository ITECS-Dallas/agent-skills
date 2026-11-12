# Windows and Mac marketplace validation

Updated: 2026-11-12. Branch: `codex/halopsa-windows11-validation`.

The full release matrix passes Windows, Apple Silicon Mac, Intel Mac and Linux. Windows 11 also passes live read-only HaloPSA calls and an actual Codex 0.18.2-to-0.18.3 upgrade. HaloPSA source PR 26 is merged; marketplace PR 33 is approved for merge after the requester accepted the repository invitation and GitHub confirmed write access. The organization production source switch remains outstanding. N-able hosted MCP has no configured token and is not certified operational.

## Fixes established by testing

| Area | Result |
| --- | --- |
| WSL shell selection | All nine stdio connectors use Git's own shell. Both hosts' manifest commands pass with failing bash first on PATH, spaces/Unicode, nested cwd, literal argv, protocol forwarding and exact exit status. |
| HaloPSA source | Windows home expansion, credential-command error redaction, native attachment attributes and portable tests are merged in [GO-MCP PR 26](https://github.com/ITECS-Dallas/GO-MCP/pull/26), commit `51f83c5c2f301cd02a16792d72af490f821e7c17`. |
| Lightweight publication | Roughly 1.5 MiB catalog; 72 separately uploaded immutable compressed assets. All GitHub asset digests match the sealed build output. The builder rejects changed executables and runtime resources and excludes untracked files. |
| Windows downloads | Real GitHub testing exposed `CRYPT_E_NO_REVOCATION_CHECK`. Windows now explicitly permits unavailable revocation information for public, SHA-pinned assets using curl's `--ssl-revoke-best-effort`. CA, hostname, validity, known revocation and both content hashes remain enforced. No retry or certificate-verification bypass. |
| Mac cleanup | Fixed Bash 3.2 exit-trap scope so atomic preparation releases its owned lock. Cold/warm/concurrent/corrupt/offline tests pass on both Mac architectures. |
| Publication integrity | Resealed the changed N-central REST launcher. Windows checkout preserves sealed billing reference bytes with LF; the builder normalizes copied text resources. Different zlib versions can produce different gzip bytes, so consumers test the exact published catalog rather than recompressing its assets. |
| Preparation errors | Missing platform entries and invalid runtime version components fail before download instead of reporting preparation success. |
| Setup/auth diagnostics | Doctor reports missing external config or auth variable names without values. The Windows configurator validates the approved `op-itecs` identity and OAuth before writing command-backed config. |

## Native results

Source matrix: [run 43305468845](https://github.com/ITECS-Dallas/GO-MCP/actions/runs/43305468845), source head `7f4f65dc3ce54f247b14fb89a1bd64a43c5d7ccc`.

Complete package/release matrix: [run 43304830005](https://github.com/ITECS-Dallas/GO-MCP/actions/runs/43304830005), package head `8bcd6535b28fa3c435714dea1eb8de35e3c04287`, published catalog `8e9095485c3ce604a9f02db496e486fb86d0ea86`. This record is a later documentation-only update. An authorized private-repository workflow checks out the exact public review commits; public-fork runner jobs were delayed.

| Environment | Coverage | Result |
| --- | --- | --- |
| Windows 11 build 26300, amd64 | All nine connectors through both manifests; PowerShell 5.1 managed-wrapper setup; 17 real public native downloads; warm/offline reuse; corruption rejection; config paths and transport | Passed |
| Windows 11, real HaloPSA identity | OAuth via `op-itecs`; both host invocations called status, authenticated agent, one-page ticket and client reads | Passed; no writes or payload retention |
| Windows 11, Claude Code 2.1.321 | Actual CLI MCP health check with isolated synthetic profile | Connected |
| Windows native CI | Native source race/vet/build; complete package, setup, HTTPS boundary and real public release tests | Passed |
| macOS 15, Apple Silicon | Native source race/vet/build; all nine connectors, complete existing package/provenance tests, HTTPS boundary and public release tests; actual Codex migration | Passed |
| macOS 15, Intel | Same complete coverage, using native amd64 executables | Passed |
| Ubuntu native CI | Source race/vet/build; HaloPSA and N-central REST shipped Linux targets; setup, publication, cache and public release tests | Passed |

The cache suites retain integrity, failed-download, missing-target, concurrency and offline negative paths. Source tests cover mutation preview, confirmation, single-write execution and readback using synthetic endpoints. Existing tests were retained and corrected for the new explicit runtime mode.

## Actual Codex CLI upgrade

Codex CLI 0.146.1 installed the original 0.18.2 HaloPSA package, removed the old marketplace source, added the lightweight Git source, refreshed it, installed 0.18.3 and discovered all 57 tools. Each run preserved external config bytes and existing plugin settings in an isolated profile.

| Host | Fresh lightweight source add | Source upgrade | Tool discovery after 0.18.3 upgrade |
| --- | --- | --- | --- |
| Windows 11 | 6.93 s | 8.77 s | 57 tools; passed |
| Apple Silicon Mac | 0.93 s | 1.50 s | 57 tools; passed |
| Intel Mac | 1.18 s | 2.78 s | 57 tools; passed |

These are measurements, not network performance guarantees. The old source repository's fresh add exceeded 55 seconds. Production users must switch sources after the organization-owned catalog and assets are published; merging a PR does not shrink old Git history or change their saved URL. The [publishing runbook](../windows-marketplace-publishing.md) owns this procedure.

## Remaining limits and access

- No live vendor records were changed. The Mac tests use synthetic HaloPSA credentials; live tenant authentication was tested on Windows only. Windows ARM64 executables are built/hash-checked, not executed on ARM hardware.
- The local Windows 11 private-CA fixture still rejects its ephemeral CA under Schannel. The full private-CA suite passes native Windows CI, and Windows 11 passes the real public GitHub path. The implementation continues rejecting untrusted certificates; OS trust stores were not changed.
- N-able: no matching N-able/N-central/GraphQL vault item title was found by the authorized metadata lookup, and `ITECS_NCENTRAL_API_TOKEN` is absent at process, user and machine scope. The requester believes no hosted API token exists. Provision the correct SSO-linked token before live handshake and inventory-coverage validation. The REST connector's JWT is a different credential.
- GitHub: the approved token authenticates as `dfaria-itecs` with `repo` and `workflow` scopes. The requester accepted the agent-skills repository invitation; GitHub now confirms `push: true`. The prior HTTP 403 was a repository-access issue and did not require broader PAT scopes.
- The [review catalog](https://github.com/dfaria-itecs/itecs-marketplace-review-20261112/tree/codex/distribution-review) and [immutable validation assets](https://github.com/dfaria-itecs/itecs-marketplace-review-20261112/releases/tag/windows-packaging-validation-2026-11-12) are public validation artifacts, not the organization production marketplace. Organization catalog publication and source migration remain outstanding. [Marketplace PR 33](https://github.com/ITECS-Dallas/agent-skills/pull/33) contains the verified changes.
- The original workspace's unrelated changes were left untouched. This machine's old HaloPSA `op.cmd` config was replaced with the OAuth-validated native managed-wrapper config after preserving a local backup; no credentials were written into the config.
