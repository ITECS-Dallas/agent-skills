# HaloPSA Windows 11 and macOS validation

Updated: 2026-11-12. Review release: 0.18.3.

The Windows configurator now uses the managed `op-itecs` identity, matching macOS and Linux. Native Windows 11 package testing covers both host launchers and generated script-backed credentials. The package review adds native Windows, macOS and Linux CI; check the pull request's completed jobs before merging.

## Changes

- Resolve `op-itecs` from PATH or an explicit absolute `-OpCommand`; remove personal `op.exe --account` setup. Do not fall back on wrapper failure.
- Execute `.cmd`, `.bat` and `.ps1` wrappers through PowerShell with literal quoted paths/arguments. Native `.exe` wrappers remain direct commands. Generated references point to the managed wrapper, not a versioned plugin-cache file.
- Preserve UTF-8 without BOM, existing-file protection, exact technician/URL/scope checks and OAuth validation. Bound the OAuth request to 30 seconds. Failed validation leaves the existing config intact.
- Rebuild only HaloPSA's six binaries from the companion GO-MCP source commit; manifests bind the revision, platform and SHA-256. Source fixes accept `~/` on Windows and withhold failed credential-command output from logs.
- Fix Windows package generation to record portable forward-slash paths and reuse the running Python interpreter for Claude generation.
- Keep generated JSON and sealed runtime text on LF across checkouts; decode file URLs and CRLF frontmatter correctly in the Windows validator. POSIX executable-bit checks remain enabled on Unix.
- Generate Claude packages from the Codex source; do not hand-edit the copies.

## Native Windows evidence

Workstation: Windows 11 Business x64, build 26300; native Python 3.14 and Windows PowerShell 5.1; Git Bash/MSYS; Go 1.27.4.

```powershell
python -X utf8 plugins/itecs-halopsa/scripts/test-windows.py
python -X utf8 claude/plugins/itecs-halopsa/scripts/test-windows.py
powershell.exe -NoProfile -NonInteractive -File plugins/itecs-halopsa/scripts/test-configure-halopsa-mcp-windows.ps1
python -X utf8 scripts/build-claude-marketplace.py --check
node scripts/validate.mjs
```

The package smoke verifies every binary checksum and the actual native executable's version and 57-tool catalog through each host's launcher. It exercises default profile and explicit override configs under spaced/Unicode paths. The setup check exercises `.ps1` and `.cmd` managed wrappers, literal apostrophes/spaces, native Go execution of generated credential commands, wrapper discovery, no persisted credential values, no BOM, refused overwrite, wrapper failure, mismatched agent/URL, bad scopes and OAuth rejection. All credentials and OAuth responses are synthetic; no vendor operations are invoked.

The companion source PR runs `go test -count=1 ./...` and `go vet ./...` on Windows 11. Its CI adds race tests and native command builds on Windows, macOS and Linux, retaining the macOS certificate-verifier regression test.

## macOS and remaining limits

`test-windows.py` retains its existing filename and now also runs natively on macOS and Linux, using HOME there. CI runs it for both Codex and Claude, plus the existing macOS/Linux configurator and launcher regression scripts. A cross-compiled macOS binary is not proof of native execution; use the completed macOS CI job as that evidence.

Windows ARM64 and Intel macOS binaries are built and checksummed, but execution on matching hardware remains a follow-up. Hosted Windows CI is separate from the Windows 11 workstation evidence. Live 1Password access and live HaloPSA write behavior are outside the synthetic checks. Review branches do not replace installed plugins or merge main.

References: [Go process execution](https://pkg.go.dev/os/exec), [PowerShell call operator](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_operators#call-operator-), [Windows runner inventory](https://github.com/actions/runner-images).
