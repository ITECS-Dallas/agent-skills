#!/usr/bin/env python3
"""Build the team packages from GO-MCP using the installed Go toolchain."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ('darwin-arm64', 'darwin-amd64', 'windows-arm64', 'windows-amd64')


def run(args, cwd):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_names(source):
    text = source.read_text()
    return sorted(set(re.findall(r'(?:readOnlyTool|writeTool)\("([\w.]+)"', text)
                      + re.findall(r'Name:\s*"([\w.]+)"', text)))


def build(source, module, command, destination, target):
    goos, goarch = target.split('-')
    destination.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, CGO_ENABLED='0', GOOS=goos, GOARCH=goarch)
    subprocess.run(['go', 'build', '-trimpath', '-ldflags=-s -w -buildid=',
                    '-o', str(destination), command], cwd=source / module,
                   env=env, check=True)
    destination.chmod(0o755)
    return {'path': destination.as_posix(), 'target': target,
            'sha256': digest(destination), 'bytes': destination.stat().st_size,
            'module': module, 'command': command}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT.parent / 'GO-MCP')
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    source = args.source.resolve()
    entries = json.loads((ROOT / 'scripts/connectors.json').read_text())
    revision = run(['git', 'rev-parse', 'HEAD'], source)
    dirty = bool(run(['git', 'status', '--porcelain'], source))
    toolchain = run(['go', 'version'], source)
    modules = ['connectors/' + e['connector'] for e in entries] + ['workflows/billing-reconciliation']
    for module in modules:
        print('Test and vet ' + module, flush=True)
        subprocess.run(['go', 'test', './...'], cwd=source / module, check=True)
        subprocess.run(['go', 'vet', './...'], cwd=source / module, check=True)
    audit = ROOT / 'plugins/itecs-billing-audit'
    (audit / 'references').mkdir(exist_ok=True)
    for name in ['billing-audit.sh', 'hosting-audit.sh']:
        shutil.copy2(source / 'scripts' / name, audit / 'scripts' / name)
    for name in ['monthly-billing-audit.md']:
        shutil.copy2(source / 'docs/runbooks' / name, audit / 'references' / name)
    shutil.copy2(source / 'skills/billing-reconciliation/SKILL.md',
                 audit / 'references/source-billing-reconciliation.md')
    # These resources are copied byte-for-byte, with their source paths recorded.
    resources = [{'path': 'scripts/' + n, 'source': 'scripts/' + n} for n in ['billing-audit.sh', 'hosting-audit.sh']]
    resources += [{'path': 'references/' + n, 'source': 'docs/runbooks/' + n} for n in ['monthly-billing-audit.md']]
    resources += [{'path': 'references/source-billing-reconciliation.md', 'source': 'skills/billing-reconciliation/SKILL.md'}]
    jobs = []
    catalogs = {}
    for entry in entries:
        module = 'connectors/' + entry['connector']
        catalogs[entry['plugin']] = tool_names(source / module / 'internal/tools/tools.go')
        for target in TARGETS:
            suffix = '.exe' if target.startswith('windows') else ''
            jobs.append((entry['plugin'], module, './cmd/mcp',
                         ROOT / 'plugins' / entry['plugin'] / 'bin' / (entry['binary'] + '-' + target + suffix), target))
            jobs.append(('itecs-billing-audit', module, './cmd/billing-report',
                         audit / 'bin' / target / (entry['connector'] + '-billing-report' + suffix), target))
    for target in TARGETS:
        suffix = '.exe' if target.startswith('windows') else ''
        jobs.append(('itecs-billing-audit', 'workflows/billing-reconciliation', './cmd/reconcile',
                     audit / 'bin' / target / ('billing-reconcile' + suffix), target))
    records = {e['plugin']: [] for e in entries}
    records['itecs-billing-audit'] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(build, source, module, command, dest, target): plugin
                   for plugin, module, command, dest, target in jobs}
        for future in concurrent.futures.as_completed(futures):
            plugin = futures[future]
            record = future.result()
            record['path'] = str(Path(record['path']).relative_to(ROOT / 'plugins' / plugin))
            records[plugin].append(record)
            print('Built ' + plugin + '/' + record['path'], flush=True)
    for plugin, binaries in records.items():
        root = ROOT / 'plugins' / plugin
        shutil.copy2(ROOT / 'scripts/templates/runtime.sh', root / 'scripts/runtime.sh')
        shutil.copy2(ROOT / 'scripts/templates/doctor.py', root / 'scripts/doctor.py')
        metadata = json.loads((root / '.codex-plugin/plugin.json').read_text())
        manifest = {'source_repository': 'https://github.com/ITECS-Dallas/GO-MCP',
                    'source_revision': revision, 'source_dirty': dirty, 'go_toolchain': toolchain,
                    'plugin': plugin, 'version': metadata['version'],
                    'build_flags': ['-trimpath', '-ldflags=-s -w -buildid='],
                    'binaries': sorted(binaries, key=lambda x: x['path'])}
        if plugin == 'itecs-billing-audit':
            manifest['resources'] = [dict(row, sha256=digest(root / row['path'])) for row in resources]
        else:
            manifest['tools'] = catalogs[plugin]
        (root / 'BUILD-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (ROOT / 'TOOL-CATALOG.json').write_text(json.dumps({'source_revision': revision, 'plugins': catalogs}, indent=2) + '\n')
    print('Built %d binaries from %s' % (len(jobs), revision), flush=True)


if __name__ == '__main__':
    main()
