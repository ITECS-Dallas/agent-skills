#!/usr/bin/env python3
"""Native Windows package smoke test with synthetic credentials; no Halo requests."""

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from doctor import discover


def run(command, cwd=None):
    return subprocess.run(command, cwd=cwd, capture_output=True,
                          encoding="utf-8", check=True, timeout=20).stdout.strip()


def main():
    if os.name != "nt":
        raise SystemExit("Run this check with native Windows Python on the test workstation.")
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))
    bash = shutil.which("bash")
    if not bash:
        raise SystemExit("Git Bash is not on PATH. Restart the terminal after installing it.")
    shell_os = run([bash, "-c", "uname -s"])
    if not shell_os.startswith(("MINGW", "MSYS", "CYGWIN")):
        raise SystemExit("The selected bash is not Git Bash/MSYS/Cygwin: " + shell_os)
    windows_binaries = [row for row in manifest["binaries"] if row["target"].startswith("windows-")]
    for row in windows_binaries:
        if hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise RuntimeError("Binary hash mismatch: " + row["path"])
    previous = {key: os.environ.get(key) for key in ("USERPROFILE", "HALOPSA_MCP_CONFIG")}
    try:
        with tempfile.TemporaryDirectory(prefix="Atlas Zoë Tech ") as temp:
            scratch = Path(temp)
            plugin = scratch / "Halo plugin"
            shutil.copytree(root / "scripts", plugin / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
            (plugin / "bin").mkdir()
            for row in windows_binaries:
                shutil.copy2(root / row["path"], plugin / row["path"])
            profile = scratch / "Windows profile"
            config = profile / ".codex/halopsa-mcp/config.json"
            config.parent.mkdir(parents=True)
            # Go executes a native program and arguments, including a spaced Python path.
            credential = [sys.executable, "-c", "print('synthetic-package-test')"]
            config.write_text(json.dumps({"servers": [{
                "id": "windows-fixture", "name": "Windows fixture",
                "base_url": "https://127.0.0.1:1/api", "token_url": "https://127.0.0.1:1/token",
                "client_id_command": credential, "client_secret_command": credential,
                "scope_command": [sys.executable, "-c", "print('read:tickets edit:tickets')"],
            }]}), encoding="utf-8")
            os.environ["USERPROFILE"] = str(profile)
            os.environ.pop("HALOPSA_MCP_CONFIG", None)
            # Exercise the same relative Bash invocation as .mcp.json, from a spaced path.
            previous_cwd = Path.cwd()
            try:
                os.chdir(plugin)
                command = [bash, "./scripts/run-halopsa-mcp"]
                version = run(command + ["-version"])
                if version != "halopsa-mcp " + manifest["version"]:
                    raise RuntimeError("Launcher version mismatch: " + version)
                expected = sorted(manifest["tools"])
                if discover(command, 30) != expected:
                    raise RuntimeError("Default USERPROFILE config discovery mismatch")
                override = scratch / "override config.json"
                shutil.copy2(config, override)
                config.unlink()
                os.environ["HALOPSA_MCP_CONFIG"] = str(override)
                if discover(command, 30) != expected:
                    raise RuntimeError("Explicit config override discovery mismatch")
            finally:
                os.chdir(previous_cwd)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    print(json.dumps({"result": "passed", "windows": platform.platform(),
                      "python_arch": platform.machine(), "bash_platform": shell_os,
                      "connector_version": manifest["version"], "tools": len(expected),
                      "config_cases": ["USERPROFILE", "HALOPSA_MCP_CONFIG"],
                      "live_credentials_tested": False, "live_halo_requests": False}, indent=2))


if __name__ == "__main__":
    main()
