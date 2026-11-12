#!/usr/bin/env python3
"""Emit a binary-free marketplace and immutable, checksummed release assets.

The output belongs in a NEW catalog repository: a plain Git clone still fetches
this source repository's historical binary blobs even after their deletion.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output, release_url):
    parsed = urlparse(release_url)
    if parsed.scheme != 'https' or parsed.hostname != 'github.com' or '/releases/download/' not in parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError('release URL must be an exact HTTPS GitHub release download base')
    output = output.resolve()
    if output == ROOT or output in ROOT.parents or output.exists():
        raise ValueError('output must be a new directory, outside existing source directories')
    catalog, assets = output / 'catalog', output / 'assets'
    assets.mkdir(parents=True)
    catalog.mkdir()
    executable_paths = []
    tracked = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    for record in tracked:
        if not record:
            continue
        metadata, name = record.split('\t', 1)
        relative = Path(name)
        if relative.parts[0] not in ('.agents', '.claude-plugin', 'plugins', 'claude') or 'bin' in relative.parts:
            continue
        target = catalog / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
        if metadata.split()[0] == '100755':
            target.chmod(0o755)
            executable_paths.append(relative.as_posix())
    for name in ('SECURITY.md', '.gitattributes', 'TOOL-CATALOG.json'):
        shutil.copy2(ROOT / name, catalog / name)
    shutil.copy2(ROOT / 'docs/distribution-README.md', catalog / 'README.md')
    records = []
    for source in sorted((ROOT / 'plugins').iterdir()):
        manifest_path = source / 'BUILD-MANIFEST.json'
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        identity = json.loads((source / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
        rows = ['\t'.join(('@package', identity['name'], identity['version']))]
        seen = set()
        for binary in manifest['binaries']:
            relative = binary['path']
            if not relative.startswith('bin/') or '\\' in relative or '..' in relative or relative in seen:
                raise ValueError('invalid or duplicate binary path: ' + relative)
            seen.add(relative)
            native = source / relative
            if digest(native) != binary['sha256'] or native.stat().st_size != binary['bytes']:
                raise ValueError('unsealed binary: ' + str(native))
            name = identity['name'] + '-' + identity['version'] + '-' + relative.replace('/', '-') + '.gz'
            archive = assets / name
            with archive.open('wb') as stream:
                with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0, compresslevel=6) as compressed:
                    with native.open('rb') as original:
                        shutil.copyfileobj(original, compressed)
            row = dict(binary, asset=name, compressed_sha256=digest(archive), compressed_bytes=archive.stat().st_size,
                       plugin=identity['name'], version=identity['version'])
            records.append(row)
            rows.append('\t'.join((relative, binary['sha256'], row['compressed_sha256'], str(binary['bytes']), str(row['compressed_bytes']), release_url.rstrip('/') + '/' + name)))
        for base in ('plugins', 'claude/plugins'):
            target = catalog / base / source.name
            if not target.exists():
                continue
            (target / 'runtime-mode').write_text('release\n', encoding='utf-8', newline='\n')
            (target / 'RUNTIME.tsv').write_text('\n'.join(rows) + '\n', encoding='utf-8', newline='\n')
        print(identity['name'] + ': sealed ' + str(len(seen)) + ' platform assets', flush=True)
    (output / 'RELEASE-ASSETS.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8', newline='\n')
    size = sum(p.stat().st_size for p in catalog.rglob('*') if p.is_file())
    summary = {'catalog_bytes': size, 'asset_count': len(records), 'asset_bytes': sum(r['compressed_bytes'] for r in records),
               'release_url': release_url, 'published': False}
    (output / 'DISTRIBUTION.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
    (output / 'EXECUTABLES.txt').write_text('\n'.join(executable_paths) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--release-url', required=True)
    args = parser.parse_args()
    build(args.output, args.release_url)
