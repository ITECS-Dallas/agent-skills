#!/usr/bin/env python3
"""Publication boundary regressions: no untracked files, no unsealed executables."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location('distribution', ROOT / 'scripts/build-distribution.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='distribution-boundary-') as temporary:
        scratch = Path(temporary)
        source = scratch / 'source'
        source.mkdir()
        subprocess.run(['git', 'init', '--quiet'], cwd=source, check=True)
        subprocess.run(['git', 'config', 'core.autocrlf', 'false'], cwd=source, check=True)
        for directory in ('.agents', '.claude-plugin', 'claude', 'docs', 'plugins/fixture/.codex-plugin', 'plugins/fixture/bin', 'plugins/fixture/scripts'):
            (source / directory).mkdir(parents=True, exist_ok=True)
        for name in ('SECURITY.md', '.gitattributes', 'TOOL-CATALOG.json', 'docs/distribution-README.md'):
            (source / name).write_text('{}\n', encoding='utf-8')
        (source / '.gitignore').write_text('.env\n', encoding='utf-8')
        plugin = source / 'plugins/fixture'
        (plugin / '.codex-plugin/plugin.json').write_text(json.dumps({'name': 'fixture', 'version': '1.0.0'}))
        native = plugin / 'bin/native'
        payload = b'synthetic test bytes, not a shipped executable\n'
        native.write_bytes(payload)
        launcher = plugin / 'scripts/launch.sh'
        launcher.write_text('#!/bin/sh\nexit 0\n', encoding='utf-8', newline='\n')
        (plugin / 'BUILD-MANIFEST.json').write_text(json.dumps({'binaries': [{'path': 'bin/native',
            'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload), 'target': 'fixture'}],
            'runtime_files': [{'path': 'scripts/launch.sh', 'sha256': hashlib.sha256(launcher.read_bytes()).hexdigest()}]}))
        (plugin / '.env').write_text('SYNTHETIC_DO_NOT_PUBLISH=1\n', encoding='utf-8')
        subprocess.run(['git', 'add', '.'], cwd=source, check=True)
        subprocess.run(['git', 'update-index', '--chmod=+x', 'plugins/fixture/scripts/launch.sh'], cwd=source, check=True)
        (plugin / 'operator-scratch.json').write_text('{"synthetic":"untracked"}', encoding='utf-8')
        module.ROOT = source
        url = 'https://github.com/example/runtime/releases/download/v1'
        first, second = scratch / 'first', scratch / 'second'
        module.build(first, url)
        module.build(second, url)
        target = first / 'catalog/plugins/fixture'
        assert not (target / 'bin').exists()
        assert not (target / '.env').exists()
        assert not (target / 'operator-scratch.json').exists()
        assert (target / 'runtime-mode').read_text().strip() == 'release'
        assert 'plugins/fixture/scripts/launch.sh' in (first / 'EXECUTABLES.txt').read_text().splitlines()
        one, two = next((first / 'assets').iterdir()), next((second / 'assets').iterdir())
        assert one.read_bytes() == two.read_bytes()
        assert gzip.decompress(one.read_bytes()) == payload
        original = launcher.read_bytes()
        launcher.write_bytes(b'changed after runtime resource sealing')
        try:
            module.build(scratch / 'unsealed-runtime', url)
        except ValueError as error:
            assert 'unsealed runtime resource' in str(error)
        else:
            raise AssertionError('unsealed runtime resource accepted')
        assert not (scratch / 'unsealed-runtime/DISTRIBUTION.json').exists()
        launcher.write_bytes(original)
        for index, bad_url in enumerate(('http://github.com/example/runtime/releases/download/v1',
                                         'https://user:credential@github.com/example/runtime/releases/download/v1')):
            try:
                module.build(scratch / ('bad-url-' + str(index)), bad_url)
            except ValueError:
                pass
            else:
                raise AssertionError('unsafe release URL accepted')
        native.write_bytes(b'changed after source sealing')
        try:
            module.build(scratch / 'unsealed', url)
        except ValueError as error:
            assert 'unsealed binary' in str(error)
        else:
            raise AssertionError('unsealed executable accepted')
        assert not (scratch / 'unsealed/DISTRIBUTION.json').exists()
    print('Distribution boundary tests passed: tracked files only, no binaries in catalog, sealed inputs, deterministic gzip, portable modes, safe HTTPS URLs.')


if __name__ == '__main__':
    main()
