#!/usr/bin/env python3
"""Test N-central first-start configuration without reading real credentials."""
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/itecs-ncentral-rest'


def run(command, env, data=''):
    return subprocess.run(command, env=env, input=data, text=True,
                          capture_output=True, timeout=15)


def executable(path, text):
    path.write_text('#!/usr/bin/env bash\n' + text)
    path.chmod(0o755)


def main():
    with tempfile.TemporaryDirectory(prefix='N-central Zoë 東京 ') as temp:
        root = Path(temp)
        plugin = root / 'plugin'
        shutil.copytree(PLUGIN / 'scripts', plugin / 'scripts')
        (plugin / 'runtime-mode').write_text('bundled\n', encoding='utf-8')
        (plugin / 'bin').mkdir()
        commands = root / 'bin with "quotes" and \\ backslash'
        commands.mkdir()
        marker = root / 'credential-command-invoked'
        executable(commands / 'op-itecs', 'touch "$MARKER"\nprintf "secret-must-never-appear" >&2\nexit 71\n')
        executable(commands / 'uname', 'case "$1" in -s) echo Linux ;; -m) echo x86_64 ;; esac\n')
        executable(plugin / 'bin/ncentral-mcp-linux-amd64', 'printf "%s\\n" "$@"\ncat\nexit 17\n')
        env = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ['PATH'],
                   HOME=str(root / 'user profile'), MARKER=str(marker))
        env.pop('NCENTRAL_MCP_CONFIG', None)
        launcher = ['bash', str(plugin / 'scripts/run-ncentral-mcp')]
        config = Path(env['HOME']) / '.codex/ncentral-mcp/config.json'
        result = run(launcher + ['--test', 'argument with spaces'], env, '{"jsonrpc":"2.0"}\n')
        assert result.returncode == 17, result.stderr
        assert result.stdout.splitlines() == ['-config', str(config), '--test', 'argument with spaces', '{"jsonrpc":"2.0"}']
        data = json.loads(config.read_text())
        server = data['servers'][0]
        assert server['base_url'] == 'https://manage.itecsonline.com'
        assert server['jwt_command'] == [str(commands / 'op-itecs'), 'read', 'op://Automation Vault/h6b4ek24qjuqdjjrvrtagfsnme/credential']
        assert stat.S_IMODE(config.stat().st_mode) == 0o600
        assert not marker.exists(), 'setup must not read any secret'
        assert 'secret-must-never-appear' not in config.read_text() + result.stdout + result.stderr
        # Never modify an existing config, even when it is malformed.
        config.write_text('existing operator config')
        assert run(launcher, env).returncode == 17
        assert config.read_text() == 'existing operator config'
        config.unlink()
        # A missing explicit override fails; no default config is created.
        explicit = dict(env, NCENTRAL_MCP_CONFIG=str(root / 'missing.json'))
        result = run(launcher, explicit)
        assert result.returncode == 2 and not config.exists()
        # A broken symlink is an operator config, not an invitation to overwrite.
        config.symlink_to(root / 'nonexistent')
        assert run(launcher, env).returncode == 2 and config.is_symlink()
        config.unlink()
        # Concurrent launches publish one complete JSON file without overwrites.
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: run(launcher, env), range(6)))
        assert all(r.returncode == 17 for r in results), [r.stderr for r in results]
        assert json.loads(config.read_text()) == data
        assert not list(config.parent.glob('.ncentral-config.*'))
        config.unlink()
        # The Windows executable path must be native, with JSON escaping intact.
        executable(commands / 'cygpath', 'printf "%s\\n" "C:/Program Files/ITECS/op-itecs.exe"\n')
        setup = ['bash', str(plugin / 'scripts/configure-defaults.sh'), str(config)]
        assert run(setup + ['windows'], env).returncode == 0
        assert json.loads(config.read_text())['servers'][0]['jwt_command'][0] == 'C:/Program Files/ITECS/op-itecs.exe'
        config.unlink()
        # Missing wrapper stops setup without a config or an alternate provider.
        (commands / 'op-itecs').unlink()
        # A minimal PATH prevents picking up another host's approved wrapper.
        minimal = root / 'minimal-bin'
        minimal.mkdir()
        for command in ('bash',):
            (minimal / command).symlink_to(shutil.which(command))
        result = run(setup + ['linux'], dict(env, PATH=str(minimal)))
        assert result.returncode == 2 and 'approved op-itecs' in result.stderr
        assert not config.exists() and not marker.exists()
    print('N-central automatic setup: secure defaults, overrides, concurrency, native paths and missing-wrapper tests passed.')


if __name__ == '__main__':
    main()
