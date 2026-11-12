#!/usr/bin/env python3
"""Exercise sealed public release assets natively, without vendor credentials."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ALIAS = 'alias.itecs-launch=!f() { if [ -n "$GIT_PREFIX" ]; then cd "$GIT_PREFIX" || exit; fi; exec /bin/bash "$@"; }; f'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    args = parser.parse_args()
    catalog = args.catalog.resolve()
    spec = importlib.util.spec_from_file_location('native_test', ROOT / 'scripts/test-native-marketplace.py')
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    entries = json.loads((ROOT / 'scripts/connectors.json').read_text(encoding='utf-8'))
    target = native.native_target()
    with tempfile.TemporaryDirectory(prefix="Public runtime Zoë O'Neil ") as temporary:
        profile = Path(temporary)
        environment = dict(os.environ, **{('USERPROFILE' if os.name == 'nt' else 'HOME'): str(profile)})
        command = [sys.executable, '-X', 'utf8', str(ROOT / 'scripts/test-native-marketplace.py'), '--catalog', str(catalog)]
        subprocess.run(command, env=environment, check=True, timeout=180)
        packages = [entry['plugin'] for entry in entries if native.supported(entry, catalog)]
        billing = catalog / 'plugins/itecs-billing-audit'
        build = json.loads((billing / 'BUILD-MANIFEST.json').read_text(encoding='utf-8'))
        billing_shipped = any(row['target'] == target for row in build['binaries'])
        if billing_shipped:
            subprocess.run(['git', '-c', ALIAS, 'itecs-launch', str(billing / 'scripts/prepare-runtime')], cwd=billing, env=environment, check=True, timeout=180)
            packages.append('itecs-billing-audit')
        sealed = {}
        for name in packages:
            package = catalog / 'plugins' / name
            assert (package / 'runtime-mode').read_text().strip() == 'release'
            metadata = json.loads((package / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
            build = json.loads((package / 'BUILD-MANIFEST.json').read_text(encoding='utf-8'))
            for row in build['binaries']:
                if row['target'] != target:
                    continue
                path = profile / '.codex/itecs-runtime' / name / metadata['version'] / row['path']
                assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']
                sealed[path] = path.stat().st_mtime_ns
        assert sealed
        offline = dict(environment, ITECS_RUNTIME_OFFLINE='1')
        subprocess.run(command, env=offline, check=True, timeout=180)
        if billing_shipped:
            for script, extra in [('run-source-report', ['halopsa', '-h']), ('run-reconcile', ['-h'])]:
                result = subprocess.run(['git', '-c', ALIAS, 'itecs-launch', str(billing / 'scripts' / script), *extra], cwd=billing, env=offline, capture_output=True, timeout=25)
                assert b'-month' in result.stdout + result.stderr or b'-source-run-id' in result.stdout + result.stderr
        assert all(path.stat().st_mtime_ns == stamp for path, stamp in sealed.items()), 'warm/offline use overwrote an executable'
        assert not list((profile / '.codex/itecs-runtime').rglob('*.lock'))
        halo = next(path for path in sealed if 'itecs-halopsa' in path.parts)
        halo.write_bytes(b'synthetic corruption test')
        package = catalog / 'plugins/itecs-halopsa'
        result = subprocess.run(['git', '-c', ALIAS, 'itecs-launch', str(package / 'scripts/prepare-runtime')], cwd=package, env=offline, capture_output=True, timeout=25)
        assert result.returncode != 0 and b'checksum mismatch' in result.stderr
        print(json.dumps({'result': 'passed', 'target': target, 'sealed_binaries': len(sealed), 'cases': ['anonymous-public-release-download', 'both-host-manifests', 'warm-cache', 'offline-cache', 'billing-help', 'immutable-cache', 'corruption-rejected'], 'vendor_calls': False}), flush=True)


if __name__ == '__main__':
    main()
