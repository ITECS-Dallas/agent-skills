#!/usr/bin/env python3
"""Native package smoke on Windows, macOS or Linux; synthetic credentials only."""

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

# Leave the installed package untouched while importing its discovery helper.
sys.dont_write_bytecode = True
from doctor import discover


def run(command, cwd=None):
    return subprocess.run(command, cwd=cwd, capture_output=True,
                          encoding="utf-8", check=True, timeout=20).stdout.strip()


def main():
    native_os = "windows" if os.name == "nt" else "darwin" if platform.system() == "Darwin" else "linux"
    profile_variable = "USERPROFILE" if native_os == "windows" else "HOME"
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))
    server = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["halopsa"]
    bash = shutil.which(server["command"])
    if not bash:
        raise SystemExit("Git Bash is not on PATH. Restart the terminal after installing it.")
    shell_os = run([bash, "-c", "uname -s"])
    if native_os == "windows" and not shell_os.startswith(("MINGW", "MSYS", "CYGWIN")):
        raise SystemExit("The selected bash is not Git Bash/MSYS/Cygwin: " + shell_os)
    for row in manifest["binaries"]:
        if hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise RuntimeError("Binary hash mismatch: " + row["path"])
    previous = {key: os.environ.get(key) for key in (profile_variable, "HALOPSA_MCP_CONFIG")}
    try:
        with tempfile.TemporaryDirectory(prefix="Atlas Zoë Tech ") as temp:
            scratch = Path(temp)
            profile = scratch / "Native profile"
            config = profile / ".codex/halopsa-mcp/config.json"
            config.parent.mkdir(parents=True)
            # Go executes a native program and arguments, including a spaced Python path.
            credential = [sys.executable, "-c", "print('synthetic-package-test')"]
            config.write_text(json.dumps({"servers": [{
                "id": "native-fixture", "name": "Native fixture",
                "base_url": "https://127.0.0.1:1/api", "token_url": "https://127.0.0.1:1/token",
                "client_id_command": credential, "client_secret_command": credential,
                "scope_command": [sys.executable, "-c", "print('read:tickets edit:tickets')"],
            }]}), encoding="utf-8")
            os.environ[profile_variable] = str(profile)
            os.environ.pop("HALOPSA_MCP_CONFIG", None)
            # Match the host's shipped stdio invocation, including an absolute Claude plugin path.
            args = [arg.replace("${CLAUDE_PLUGIN_ROOT}", str(root)) for arg in server["args"]]
            previous_cwd = Path.cwd()
            try:
                os.chdir(root / server["cwd"] if "cwd" in server else scratch)
                command = [bash, *args]
                version = run(command + ["-version"])
                if version != "halopsa-mcp " + manifest["version"]:
                    raise RuntimeError("Launcher version mismatch: " + version)
                expected = sorted(manifest["tools"])
                if discover(command, 30) != expected:
                    raise RuntimeError("Default profile config discovery mismatch")
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
    print(json.dumps({"result": "passed", "platform": platform.platform(),
                      "python_arch": platform.machine(), "bash_platform": shell_os,
                      "mcp_host": "codex" if "cwd" in server else "claude",
                      "connector_version": manifest["version"], "tools": len(expected),
                      "config_cases": [profile_variable, "HALOPSA_MCP_CONFIG"],
                      "live_credentials_tested": False, "live_halo_requests": False}, indent=2))


if __name__ == "__main__":
    main()
