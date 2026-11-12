# Production publication and N-able setup

Updated: 2026-11-12.

The organization runtime release is published and checksum-verified. The small catalog is staged without binary history. N-able authentication and the actual Claude HTTP connection pass, but the current SSO identity has no organizations/assets visible, matching the requester's empty portal.

## Publication

- Source: merged agent-skills main commit `04f8f2b020d57ab95821ceb53c64201d0f203ee8`; all four native post-merge CI jobs passed.
- Runtime release: [windows-packaging-2026-11-12](https://github.com/ITECS-Dallas/agent-skills/releases/tag/windows-packaging-2026-11-12), release ID `443559746`. Published only after GitHub reported the expected SHA-256 and byte size for every native asset. Contains 72 immutable native gzip assets plus `RELEASE-ASSETS.json`, `DISTRIBUTION.json`, `EXECUTABLES.txt` and `SHA256SUMS`.
- Catalog: [staged main](https://github.com/dfaria-itecs/itecs-marketplace-review-20261112/tree/main), commit `2e42669`, about 1.5 MiB. Its executable Git modes are restored from the emitted plan, and all runtime entries use the organization release URLs. No vendor executables or credentials are in its Git history.
- Real anonymous downloads from the production organization URLs passed on Windows 11: all 17 native connector/billing binaries, both host manifests, warm/offline reuse, unchanged cache files and corrupted-cache rejection. These are the same sealed native bytes already executed by the four-platform release matrix; no vendor calls were made in this publication test.
- Windows PowerShell pipeline input adds CRLF that Git's `update-index --stdin` can interpret as part of the pathname. The runbook now restores modes with one explicit pathname per invocation; this was executed successfully while preparing the real catalog.
- Production source registration is not complete. The GitHub identity can write agent-skills but the organization-repository creation endpoint returned 404. An organization owner must create the separate empty public `ITECS-Dallas/agent-skills-marketplace` repository, or import the binary-free staged catalog, and grant publishing access. The existing `agent-skills` source repository is not this new repository; a full clone still includes its old binary history.
- Existing user marketplace sources have not been changed while the organization catalog is unavailable. Preserve external configs and plugin settings during the one-time switch, then rerun fresh add/upgrade against the organization URL.

## N-able account validation

- The requester created the SSO-linked token in N-able's API Token Management portal and stored it in Automation Vault. Only the exact approved credential field was read through `op-itecs`; no credential values were logged, committed, or written into configuration or Markdown.
- The fixed `https://api.n-able.com/mcp-read-only` endpoint accepts authentication and negotiates protocol `2025-11-25`. The service advertises 16 entries with 15 unique tool names; its duplicate bulk-details entry is vendor-provided.
- A Python default User-Agent received Cloudflare error 1010 before MCP authentication. An honest ITECS application User-Agent reached the supported API normally. The actual Claude Code 2.1.321 HTTP health check also reports Connected. Its isolated files were scanned to confirm the credential was not persisted.
- Read-only `list_organisational_structure` and `list_asset_inventory` queries both returned totalCount 0 with no next page and no GraphQL errors. This is visibility under the current identity, not evidence that ITECS has no devices. The requester confirms Assets is empty/unavailable in the portal too; known-device validation remains blocked by account/environment access.
- Per [N-able prerequisites](https://documentation.n-able.com/N-central/userguide/Content/Introduction-GettingStarted/access-ecoverse-features.htm), an administrator must check N-central 2025.2+, the correct N-able Login association, Ecoverse role permissions, and Analytics/Data Export for on-premises environments. Linking N-able Login is documented as irreversible. No SSO provider, role, data-export setting, customer permission or live device was changed by this work.
- Machine-local Codex/Claude launchers resolve the installed application, read the approved vault field into the child process environment, and restore the launcher's environment afterward. Both executable/credential checks pass. They refuse to launch while the target app is already running; the user must fully quit and relaunch to supply a new desktop process environment. Nothing is stored in the Windows user/machine token environment or a secret-bearing config file.

The public source/skills continue to contain only environment references. Fleet coverage and one known device must be verified after the administrator resolves visibility; do not report readiness from handshake success alone.
