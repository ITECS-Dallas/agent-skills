#!/usr/bin/env python3
"""Generate the Claude Code marketplace from the Codex marketplace.

The Codex marketplace (.agents/plugins/marketplace.json and plugins/<name>)
is the source. Claude Code needs a different plugin manifest and an MCP
config that starts the launcher from ${CLAUDE_PLUGIN_ROOT}, so each plugin is
copied to claude/plugins/<name> with a .claude-plugin/plugin.json and a
Claude .mcp.json, and .claude-plugin/marketplace.json lists them. Files are
real copies because Claude's plugin cache drops symlinks; Git stores the
identical binaries once, so the copies do not grow the repository history.

  python3 scripts/build-claude-marketplace.py          # regenerate
  python3 scripts/build-claude-marketplace.py --check  # fail if out of date

Never edit claude/ by hand; change plugins/ and regenerate.
"""
import argparse
import filecmp
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.mcp.json'}
MANIFEST_KEYS = ('name', 'version', 'description', 'author', 'homepage', 'repository', 'license', 'keywords')


def claude_servers(mcp_file):
    servers = {}
    for name, cfg in json.loads(mcp_file.read_text())['mcpServers'].items():
        if 'url' in cfg:
            # Codex remote server: url plus bearer_token_env_var. Claude needs
            # an explicit transport type and expands ${VAR} in headers.
            server = {'type': cfg.get('type', 'http'), 'url': cfg['url']}
            headers = dict(cfg.get('headers', {}))
            if cfg.get('bearer_token_env_var'):
                headers['Authorization'] = 'Bearer ${' + cfg['bearer_token_env_var'] + '}'
            if headers:
                server['headers'] = headers
            servers[name] = server
            continue
        args = ['${CLAUDE_PLUGIN_ROOT}/' + a[2:] if a.startswith('./') else a for a in cfg.get('args', [])]
        # Claude starts stdio servers with the parent environment. env_vars is a Codex-only allowlist.
        servers[name] = {**{k: v for k, v in cfg.items() if k not in {'cwd', 'env_vars'}}, 'args': args}
    return {'mcpServers': servers}


def generate(out):
    codex = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
    entries = []
    for item in codex['plugins']:
        src = (ROOT / item['source']['path']).resolve()
        meta = json.loads((src / '.codex-plugin/plugin.json').read_text())
        dst = out / 'claude/plugins' / item['name']
        dst.mkdir(parents=True)
        for child in sorted(src.iterdir()):
            if child.name in SKIP:
                continue
            if child.is_dir():
                shutil.copytree(child, dst / child.name, symlinks=False,
                                ignore=shutil.ignore_patterns('__pycache__', '.DS_Store'))
            else:
                shutil.copy2(child, dst / child.name)
        (dst / '.claude-plugin').mkdir()
        manifest = {k: meta[k] for k in MANIFEST_KEYS if k in meta}
        (dst / '.claude-plugin/plugin.json').write_text(json.dumps(manifest, indent=2) + '\n')
        if (src / '.mcp.json').exists():
            (dst / '.mcp.json').write_text(json.dumps(claude_servers(src / '.mcp.json'), indent=2) + '\n')
        entry = {'name': item['name'], 'source': './claude/plugins/' + item['name'],
                 'description': meta.get('description', ''), 'version': meta.get('version')}
        if item.get('category'):
            entry['category'] = item['category']
        entries.append(entry)
    marketplace = {
        'name': codex['name'],
        'owner': {'name': 'ITECS-Dallas'},
        'metadata': {'description': 'ITECS plugins, skills and connectors for Claude Code. Generated from the Codex marketplace by scripts/build-claude-marketplace.py.'},
        'plugins': entries,
    }
    (out / '.claude-plugin').mkdir(parents=True, exist_ok=True)
    (out / '.claude-plugin/marketplace.json').write_text(json.dumps(marketplace, indent=2) + '\n')
    return len(entries)


def tree(root):
    return sorted(p.relative_to(root) for p in root.rglob('*') if p.is_file() and p.name != '.DS_Store' and '__pycache__' not in p.parts)


def differences(expected, actual):
    problems = []
    for base in ('claude', '.claude-plugin'):
        want, have = expected / base, actual / base
        want_files = tree(want) if want.exists() else []
        have_files = tree(have) if have.exists() else []
        for rel in sorted(set(want_files) ^ set(have_files)):
            problems.append(('missing ' if rel in want_files else 'extra ') + str(Path(base) / rel))
        for rel in sorted(set(want_files) & set(have_files)):
            a, b = want / rel, have / rel
            if not filecmp.cmp(a, b, shallow=False) or (a.stat().st_mode & 0o111) != (b.stat().st_mode & 0o111):
                problems.append('stale ' + str(Path(base) / rel))
    return problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fail if the committed Claude marketplace is out of date')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        count = generate(out)
        if args.check:
            problems = differences(out, ROOT)
            if problems:
                print('Claude marketplace is out of date; run python3 scripts/build-claude-marketplace.py', file=sys.stderr)
                for problem in problems[:20]:
                    print('  ' + problem, file=sys.stderr)
                sys.exit(1)
            print('Claude marketplace is current: %d plugins' % count)
            return
        for base in ('claude', '.claude-plugin'):
            if (ROOT / base).exists():
                shutil.rmtree(ROOT / base)
            shutil.copytree(out / base, ROOT / base)
    print('Claude marketplace written: %d plugins in claude/plugins' % count)


if __name__ == '__main__':
    main()
