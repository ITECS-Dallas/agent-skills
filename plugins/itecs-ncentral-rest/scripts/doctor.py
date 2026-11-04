#!/usr/bin/env python3
"""Optional local package diagnostics. --discover performs MCP discovery only."""
import argparse
import json
import os
from pathlib import Path
import platform
import queue
import subprocess
import threading
import time


def discover(command, timeout):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, bufsize=1)
    messages = queue.Queue()

    def read():
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except ValueError:
                continue
        messages.put(None)

    threading.Thread(target=read, daemon=True).start()
    deadline = time.monotonic() + timeout

    def send(message):
        process.stdin.write(json.dumps(message) + '\n')
        process.stdin.flush()

    def response(identifier):
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('MCP discovery timed out')
            try:
                message = messages.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError('MCP discovery timed out') from None
            if message is None:
                raise RuntimeError('MCP process exited before discovery completed')
            if message.get('id') == identifier:
                if 'error' in message:
                    raise RuntimeError('MCP discovery returned a protocol error')
                return message['result']

    try:
        send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': '2025-03-26', 'capabilities': {},
            'clientInfo': {'name': 'itecs-package-doctor', 'version': '1.0'}}})
        response(1)
        send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        names, cursor, request_id = [], None, 2
        while True:
            send({'jsonrpc': '2.0', 'id': request_id, 'method': 'tools/list',
                  'params': {'cursor': cursor} if cursor else {}})
            result = response(request_id)
            names.extend(tool['name'] for tool in result.get('tools', []))
            cursor = result.get('nextCursor')
            if not cursor:
                return sorted(names)
            request_id += 1
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        for stream in (process.stdin, process.stdout):
            if stream:
                stream.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--discover', action='store_true')
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('--config', type=Path, help='Use this existing connector config')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / '.codex-plugin/plugin.json').read_text())
    result = {'plugin': manifest['name'], 'version': manifest['version'],
              'platform': platform.system() + '-' + platform.machine()}
    build = root / 'BUILD-MANIFEST.json'
    if build.exists():
        data = json.loads(build.read_text())
        result['source_revision'] = data.get('source_revision')
        result['source_dirty'] = data.get('source_dirty')
        result['missing_binaries'] = [item['path'] for item in data['binaries']
                                      if not (root / item['path']).is_file()]
    connector = root / 'connector.json'
    if connector.exists():
        data = json.loads(connector.read_text())
        user = Path(os.environ.get('USERPROFILE', str(Path.home()))) if os.name == 'nt' else Path.home()
        config = args.config or Path(os.environ.get(data['config_env'], str(user / '.codex' / (data['connector'] + '-mcp') / 'config.json')))
        result['config_path'] = str(config)
        result['config_exists'] = config.is_file()
        if args.discover:
            command = [str(root / 'bin' / (data['binary'] + '-' +
                ('windows' if os.name == 'nt' else 'darwin' if platform.system() == 'Darwin' else 'linux') + '-' +
                ('arm64' if platform.machine().lower() in ('arm64', 'aarch64') else 'amd64') +
                ('.exe' if os.name == 'nt' else ''))), '-config', str(config)]
            try:
                result['tools'] = discover(command, args.timeout)
                result['tool_count'] = len(result['tools'])
                result['discovery'] = 'ok'
            except (OSError, RuntimeError, TimeoutError, KeyError, BrokenPipeError):
                result['discovery'] = 'failed; inspect config and launcher startup locally'
    elif args.discover:
        result['discovery'] = 'This command package has no MCP server; use its report and audit commands.'
    print(json.dumps(result, indent=2))
    return 1 if str(result.get('discovery', '')).startswith('failed') else 0


if __name__ == '__main__':
    raise SystemExit(main())
