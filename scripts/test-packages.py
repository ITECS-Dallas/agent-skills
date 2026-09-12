#!/usr/bin/env python3
"""Exercise package integrity, real local MCP discovery and launcher dispatch."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'GO-MCP'


def execute(command, **kwargs):
    return subprocess.run(command, capture_output=True, text=True, timeout=40, **kwargs)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def executable(path, content):
    path.write_text(content)
    path.chmod(0o755)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plugin', help='Test one connector plugin without requiring other platforms')
    args = parser.parse_args()
    entries = json.loads((ROOT / 'scripts/connectors.json').read_text())
    if args.plugin:
        entries = [entry for entry in entries if entry['plugin'] == args.plugin]
        if not entries:
            parser.error('unknown connector plugin: ' + args.plugin)
    catalog = json.loads((ROOT / 'TOOL-CATALOG.json').read_text())
    with tempfile.TemporaryDirectory(prefix='itecs package tests ') as temp:
        tmp = Path(temp)
        for entry in entries:
            plugin = ROOT / 'plugins' / entry['plugin']
            manifest = json.loads((plugin / 'BUILD-MANIFEST.json').read_text())
            metadata = json.loads((plugin / '.codex-plugin/plugin.json').read_text())
            check(manifest['version'] == metadata['version'], 'build version: ' + entry['plugin'])
            if entry['plugin'] == 'itecs-halopsa':
                check(bool(manifest.get('runtime_files')), 'missing RELAY runtime manifest')
                runtime = plugin / 'runtime/itecs-relay'
                actual = {str(path.relative_to(plugin)) for path in runtime.rglob('*')
                          if path.is_file() and '__pycache__' not in path.parts}
                check(actual == {row['path'] for row in manifest['runtime_files']}, 'RELAY runtime file manifest is incomplete')
                result = execute(['python3', '-m', 'relay', '--help'], cwd=runtime)
                check(result.returncode == 0 and 'inspect' in result.stdout, 'packaged RELAY entrypoint does not run')
            for record in manifest.get('runtime_files', []):
                path = plugin / record['path']
                check(hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], 'runtime hash: ' + str(path))
            expected_targets = {'darwin-arm64', 'darwin-amd64', 'windows-arm64', 'windows-amd64'} | set(entry.get('additional_targets', []))
            check({binary['target'] for binary in manifest['binaries']} == expected_targets, 'packaged target set: ' + entry['plugin'])
            for binary in manifest['binaries']:
                path = plugin / binary['path']
                check(hashlib.sha256(path.read_bytes()).hexdigest() == binary['sha256'], 'binary hash: ' + str(path))
                info = execute(['go', 'version', '-m', str(path)])
                check('vcs.revision=' + manifest['source_revision'] in info.stdout, 'embedded source revision: ' + str(path))
                goos, goarch = binary['target'].split('-')
                for setting in ['GOOS=' + goos, 'GOARCH=' + goarch, 'CGO_ENABLED=0']:
                    check(setting in info.stdout, 'embedded build target ' + setting + ': ' + str(path))
            check((plugin / 'scripts/runtime.sh').read_bytes() == (ROOT / 'scripts/templates/runtime.sh').read_bytes(), 'runtime template drift')
            check((plugin / 'scripts/doctor.py').read_bytes() == (ROOT / 'scripts/templates/doctor.py').read_bytes(), 'doctor template drift')
            # Fake credentials and unreachable loopback endpoints: no live vendor access.
            example = plugin / 'config.example.json'
            if not example.exists():
                example = SOURCE / 'connectors' / entry['connector'] / 'config.example.json'
            config = json.loads(example.read_text())
            for server in config['servers']:
                for key, value in list(server.items()):
                    if key.endswith('_command'):
                        server[key] = ['/usr/bin/printf', 'fixture']
                    elif 'url' in key and isinstance(value, str):
                        server[key] = 'https://127.0.0.1:1'
            fixture = tmp / (entry['connector'] + '.json')
            fixture.write_text(json.dumps(config))
            result = execute(['python3', str(plugin / 'scripts/doctor.py'), '--discover', '--config', str(fixture), '--timeout', '8'])
            check(result.returncode == 0, entry['plugin'] + ' discovery: ' + result.stdout + result.stderr)
            data = json.loads(result.stdout)
            check(data['tools'] == catalog['plugins'][entry['plugin']], entry['plugin'] + ' tool catalog mismatch')
            check('fixture' not in result.stdout, 'doctor exposed fixture credential')
            print(entry['plugin'] + ': %d actual MCP tools' % data['tool_count'], flush=True)
            if entry['plugin'] == 'itecs-halopsa':
                for script in ['test-run-halopsa-mcp.sh', 'test-configure-halopsa-mcp-macos.sh', 'test-configure-halopsa-mcp-linux.sh']:
                    setup = execute(['bash', str(plugin / 'scripts' / script)])
                    check(setup.returncode == 0, script + ': ' + setup.stdout + setup.stderr)
                    print(setup.stdout.strip(), flush=True)

            # Simulate Windows path and binary selection without executing a Windows binary.
            clone = tmp / entry['plugin']
            shutil.copytree(plugin / 'scripts', clone / 'scripts')
            (clone / 'bin').mkdir()
            fake_path = clone / 'fake-path'
            fake_path.mkdir()
            executable(fake_path / 'uname', '#!/usr/bin/env bash\ncase "$1" in -s) echo MINGW64_NT ;; -m) echo x86_64 ;; esac\n')
            profile = clone / 'Windows profile with spaces'
            config_dir = profile / '.codex' / (entry['connector'] + '-mcp')
            config_dir.mkdir(parents=True)
            (config_dir / 'config.json').write_text('{}')
            executable(fake_path / 'cygpath', '#!/usr/bin/env bash\nprintf "%s\\n" "$FAKE_PROFILE"\n')
            binary = clone / 'bin' / (entry['binary'] + '-windows-amd64.exe')
            executable(binary, '#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            env = dict(os.environ, PATH=str(fake_path) + os.pathsep + os.environ['PATH'],
                       USERPROFILE='windows-fixture', FAKE_PROFILE=str(profile))
            env.pop(entry['config_env'], None)
            launcher = clone / 'scripts' / ('run-' + entry['connector'] + '-mcp')
            result = execute(['bash', str(launcher)], env=env)
            check(result.returncode == 0 and str(config_dir / 'config.json') in result.stdout, 'Windows config selection: ' + result.stderr)
            env[entry['config_env']] = str(fixture)
            result = execute(['bash', str(launcher)], env=env)
            check(result.returncode == 0 and result.stdout.splitlines() == ['-config', str(fixture)], 'config override selection')

            # Verify both Linux architectures, config paths with spaces, protocol stdin,
            # argument forwarding and exit status without executing cross-built binaries.
            for target in entry.get('additional_targets', []):
                os_name, arch = target.split('-')
                check(os_name == 'linux', 'unhandled dispatch test target: ' + target)
                executable(fake_path / 'uname', '#!/usr/bin/env bash\ncase "$1" in -s) echo Linux ;; -m) echo ' + ('aarch64' if arch == 'arm64' else 'x86_64') + ' ;; esac\n')
                executable(clone / 'bin' / (entry['binary'] + '-' + target), '#!/usr/bin/env bash\nprintf "%s\\n" "$@"\ncat\nexit 17\n')
                env['HOME'] = str(profile)
                env.pop(entry['config_env'], None)
                result = execute(['bash', str(launcher), '--example', 'argument with spaces'], env=env, input='{"id":1}\n')
                check(result.returncode == 17 and result.stdout.splitlines() == ['-config', str(config_dir / 'config.json'), '--example', 'argument with spaces', '{"id":1}'], 'Linux launcher transport: ' + target + result.stderr)
                env[entry['config_env']] = str(fixture)
                result = execute(['bash', str(launcher)], env=env, input='')
                check(result.returncode == 17 and result.stdout.splitlines() == ['-config', str(fixture)], 'Linux config override: ' + target)

        if not args.plugin:
            test_audit(tmp, entries)

        test_discovery(tmp)
    print('Package integrity, MCP discovery, platform dispatch, setup and diagnostic tests passed.')


def test_audit(tmp, entries):
    audit = ROOT / 'plugins/itecs-billing-audit'
    manifest = json.loads((audit / 'BUILD-MANIFEST.json').read_text())
    for record in manifest['binaries'] + manifest['resources']:
        path = audit / record['path']
        check(hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], 'audit artifact hash: ' + str(path))
        if 'target' in record:
            info = execute(['go', 'version', '-m', str(path)])
            check('vcs.revision=' + manifest['source_revision'] in info.stdout, 'audit embedded source revision: ' + str(path))
    for entry in entries:
        result = execute(['bash', str(audit / 'scripts/run-source-report'), entry['connector'], '-h'])
        check('-month' in result.stdout + result.stderr, 'source report help did not execute: ' + entry['connector'] + result.stderr)
    result = execute(['bash', str(audit / 'scripts/run-reconcile'), '-h'])
    check('-source-run-id' in result.stdout + result.stderr, 'reconciler help did not execute')
    env = dict(os.environ, DRY_RUN='1', MONTH='2026-09', SOURCES='all',
               REPORTS_DIR=str(tmp / 'dry reports'), CLIENT_CROSSWALK=str(tmp / 'crosswalk.json'),
               SERVICE_LINE_MAPPING=str(tmp / 'service-mapping.json'))
    result = execute(['bash', str(audit / 'scripts/run-billing-audit')], env=env, cwd=tmp)
    check(result.returncode == 0, 'packaged audit dry run: ' + result.stdout + result.stderr)
    check('go run' not in result.stdout and 'billing-reconcile' in result.stdout, 'audit used a developer checkout')
    check(not (tmp / 'dry reports').exists(), 'dry run wrote reports')


def test_discovery(tmp):
    # Discovery handles a paginated tool list and a stalled process.
    spec = importlib.util.spec_from_file_location('doctor', ROOT / 'scripts/templates/doctor.py')
    doctor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctor)
    server = tmp / 'fake-mcp.py'
    server.write_text('''import json, sys
for line in sys.stdin:
 r=json.loads(line)
 if 'id' not in r: continue
 if r['method']=='initialize': value={}
 elif r.get('params',{}).get('cursor'): value={'tools':[{'name':'second'}]}
 else: value={'tools':[{'name':'first'}], 'nextCursor':'next'}
 print(json.dumps({'jsonrpc':'2.0','id':r['id'],'result':value}),flush=True)
''')
    check(doctor.discover(['python3', str(server)], 3) == ['first', 'second'], 'discovery pagination')
    try:
        doctor.discover(['python3', '-c', 'import time; time.sleep(10)'], 0.1)
        raise AssertionError('discovery timeout was ignored')
    except TimeoutError:
        pass


if __name__ == '__main__':
    main()
