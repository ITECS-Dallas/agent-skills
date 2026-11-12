#!/usr/bin/env python3
"""Exercise the shipped host invocation with a hostile bash on PATH. No vendor calls."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def native_target():
    system = {'Windows': 'windows', 'Darwin': 'darwin', 'Linux': 'linux'}[platform.system()]
    arch = {'AMD64': 'amd64', 'x86_64': 'amd64', 'arm64': 'arm64', 'aarch64': 'arm64'}[platform.machine()]
    return system + '-' + arch


def supported(entry, catalog):
    build = json.loads((catalog / 'plugins' / entry['plugin'] / 'BUILD-MANIFEST.json').read_text(encoding='utf-8'))
    return any(binary['target'] == native_target() for binary in build['binaries'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configs', type=Path, default=ROOT / 'tests/runtime-configs')
    parser.add_argument('--catalog', type=Path, default=ROOT)
    parser.add_argument('--plugin')
    args = parser.parse_args()
    entries = json.loads((ROOT / 'scripts/connectors.json').read_text(encoding='utf-8'))
    if args.plugin:
        entries = [e for e in entries if e['plugin'] == args.plugin]
    spec = importlib.util.spec_from_file_location('doctor', ROOT / 'scripts/templates/doctor.py')
    doctor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctor)
    with tempfile.TemporaryDirectory(prefix="MCP Zoë O'Neil ") as temp:
        scratch = Path(temp)
        tripwire = scratch / 'wrong-bash'
        tripwire.mkdir()
        if os.name == 'nt':
            (tripwire / 'bash.cmd').write_text('@echo WSL_PATH_WAS_USED\r\n@exit /b 99\r\n')
        else:
            (tripwire / 'bash').write_text('#!/bin/sh\necho WRONG_BASH_ON_PATH >&2\nexit 99\n')
            (tripwire / 'bash').chmod(0o755)
        env = dict(os.environ, PATH=str(tripwire) + os.pathsep + os.environ['PATH'])
        project = scratch / 'project'
        subprocess.run(['git', 'init', '--quiet', str(project)], check=True)
        nested = project / "nested O'Neil"
        nested.mkdir()
        transport = scratch / 'transport.sh'
        transport.write_text('#!/bin/bash\n"$ITECS_TEST_PY" -X utf8 -c "import os; print(os.getcwd())"\nprintf "%s\\n" "$@"\ncat\nexit 17\n', encoding='utf-8', newline='\n')
        first = entries[0]
        server = json.loads((ROOT / 'plugins' / first['plugin'] / '.mcp.json').read_text(encoding='utf-8'))['mcpServers'][first['server']]
        command = [server['command'], *server['args'][:3], str(transport), 'spaces & quotes', "O'Neil", 'literal $HOME']
        forwarded = subprocess.run(command, cwd=nested, env=dict(env, ITECS_TEST_PY=sys.executable),
                                   input='{"id":1}\n', text=True, encoding='utf-8', capture_output=True, timeout=15)
        assert forwarded.returncode == 17 and not forwarded.stderr
        assert forwarded.stdout.splitlines() == [str(nested.resolve()), 'spaces & quotes', "O'Neil", 'literal $HOME', '{"id":1}']
        print('Git dispatch preserves nested working directory, literal argv, stdin/stdout and exit status.', flush=True)
        for entry in entries:
            if not supported(entry, args.catalog):
                print(json.dumps({'plugin': entry['plugin'], 'target': native_target(), 'result': 'not shipped'}), flush=True)
                continue
            config = json.loads((args.configs / (entry['connector'] + '.json')).read_text(encoding='utf-8'))
            for server in config['servers']:
                for key, value in list(server.items()):
                    if key.endswith('_command'):
                        server[key] = [sys.executable, '-c', "print('synthetic-native-test')"]
                    elif 'url' in key and isinstance(value, str):
                        server[key] = 'https://127.0.0.1:1'
            fixture = scratch / (entry['connector'] + '.json')
            fixture.write_text(json.dumps(config), encoding='utf-8')
            env[entry['config_env']] = str(fixture)
            for base in ('plugins', 'claude/plugins'):
                root = (args.catalog / base / entry['plugin']).resolve()
                server = json.loads((root / '.mcp.json').read_text(encoding='utf-8'))['mcpServers'][entry['server']]
                command = [server['command'], *server['args']]
                command = [arg.replace('${CLAUDE_PLUGIN_ROOT}', str(root)) for arg in command]
                expected = sorted(json.loads((root / 'BUILD-MANIFEST.json').read_text(encoding='utf-8'))['tools'])
                actual = doctor.discover(command, 40, cwd=root, env=env, stderr=sys.stderr)
                if actual != expected:
                    raise AssertionError(entry['plugin'] + ': tool catalog mismatch')
                print(json.dumps({'plugin': entry['plugin'], 'host': 'codex' if base == 'plugins' else 'claude',
                                  'platform': platform.platform(), 'tools': len(actual), 'wrong_bash_on_path': True,
                                  'result': 'passed', 'vendor_calls': False}), flush=True)


if __name__ == '__main__':
    main()
