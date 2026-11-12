#!/usr/bin/env python3
"""Native thin-package tests against a temporary HTTPS artifact server; no vendor calls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import http.server
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ALIAS = 'alias.itecs-launch=!f() { if [ -n "$GIT_PREFIX" ]; then cd "$GIT_PREFIX" || exit; fi; exec /bin/bash "$@"; }; f'


def tool(name):
    found = shutil.which(name)
    if found:
        return found
    if os.name == 'nt':
        candidate = Path(os.environ['ProgramFiles']) / 'Git/usr/bin' / (name + '.exe')
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError(name + ' is required for the local HTTPS test')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--distribution', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('doctor', ROOT / 'scripts/templates/doctor.py')
    doctor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctor)
    assets = (args.distribution / 'assets').resolve()
    state = {'requests': 0, 'fail': False}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            state['requests'] += 1
            name = self.path.lstrip('/')
            path = assets / name
            if state['fail'] or '/' in name or not path.is_file():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Length', str(path.stat().st_size))
            self.end_headers()
            with path.open('rb') as stream:
                shutil.copyfileobj(stream, self.wfile)

        def log_message(self, *_):
            pass

    with tempfile.TemporaryDirectory(prefix="Release Zoë O'Neil ") as temporary:
        scratch = Path(temporary)
        cert, key = scratch / 'ca.pem', scratch / 'key.pem'
        ca_config = scratch / 'openssl.cnf'
        ca_config.write_text('[req]\nprompt=no\ndistinguished_name=dn\nx509_extensions=ext\n[dn]\nCN=127.0.0.1\n[ext]\nsubjectAltName=IP:127.0.0.1\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,digitalSignature,keyEncipherment,keyCertSign\n', encoding='utf-8')
        subprocess.run([tool('openssl'), 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                        '-keyout', str(key), '-out', str(cert), '-config', str(ca_config)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=20)
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            package = scratch / 'package'
            shutil.copytree(args.distribution / 'catalog/plugins/itecs-halopsa', package)
            rows = (package / 'RUNTIME.tsv').read_text(encoding='utf-8').splitlines()
            for index, row in enumerate(rows):
                if not row.startswith('@'):
                    fields = row.split('\t')
                    fields[-1] = 'https://127.0.0.1:' + str(server.server_port) + '/' + fields[-1].rsplit('/', 1)[-1]
                    rows[index] = '\t'.join(fields)
            sealed = '\n'.join(rows) + '\n'
            (package / 'RUNTIME.tsv').write_text(sealed, encoding='utf-8', newline='\n')
            # Trust this test CA only in a temporary curl wrapper, never in OS trust.
            tools = scratch / 'tools'
            tools.mkdir()
            quote = lambda value: "'" + str(value).replace("'", "'\\''") + "'"
            curl = tools / 'curl'
            curl.write_text('#!/bin/sh\nexec ' + quote(tool('curl')) + ' --cacert ' + quote(cert) + ' "$@"\n', encoding='utf-8', newline='\n')
            curl.chmod(0o755)
            config = scratch / 'config.json'
            credential = [sys.executable, '-c', "print('synthetic-release-test')"]
            config.write_text(json.dumps({'servers': [{'id': 'fixture', 'base_url': 'https://127.0.0.1:1/api',
                'token_url': 'https://127.0.0.1:1/token', 'client_id_command': credential,
                'client_secret_command': credential, 'scope': 'read:tickets'}]}), encoding='utf-8')
            environment = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ['PATH'], HALOPSA_MCP_CONFIG=str(config))
            profile_key = 'USERPROFILE' if os.name == 'nt' else 'HOME'
            command = ['git', '-c', ALIAS, 'itecs-launch', str(package / 'scripts/run-halopsa-mcp')]
            expected = sorted(json.loads((package / 'BUILD-MANIFEST.json').read_text())['tools'])

            def profile(name):
                home = scratch / name
                home.mkdir()
                return dict(environment, **{profile_key: str(home)})

            warm = profile('warm')
            for _ in range(2):
                assert doctor.discover(command, 40, cwd=package, env=warm) == expected
            assert state['requests'] == 1, state
            cache = Path(warm[profile_key]) / '.codex/itecs-runtime'
            binary = next(p for p in cache.rglob('*') if p.is_file())
            binary.write_bytes(b'corrupt-native-cache')
            result = subprocess.run(command + ['-version'], cwd=package, env=warm, capture_output=True, timeout=20)
            assert result.returncode != 0 and b'checksum mismatch' in result.stderr
            assert state['requests'] == 1, 'corrupt cache silently redownloaded'
            cold = profile('concurrent')
            with ThreadPoolExecutor(max_workers=2) as pool:
                checks = [pool.submit(doctor.discover, command, 40, package, cold) for _ in range(2)]
                assert all(check.result() == expected for check in checks)
            assert state['requests'] == 2, 'concurrent preparation downloaded twice'
            offline = profile('offline')
            offline['ITECS_RUNTIME_OFFLINE'] = '1'
            result = subprocess.run(command + ['-version'], cwd=package, env=offline, capture_output=True, timeout=20)
            assert result.returncode != 0 and b'offline command' in result.stderr
            assert state['requests'] == 2
            for field, label in ((1, 'native-checksum'), (2, 'gzip-checksum'), (3, 'native-size')):
                changed = []
                for row in rows:
                    fields = row.split('\t')
                    if not row.startswith('@'):
                        fields[field] = '1' if field == 3 else '0' * 64
                    changed.append('\t'.join(fields))
                (package / 'RUNTIME.tsv').write_text('\n'.join(changed) + '\n', encoding='utf-8', newline='\n')
                case = profile(label)
                result = subprocess.run(command + ['-version'], cwd=package, env=case, capture_output=True, timeout=25)
                assert result.returncode != 0 and b'checksum mismatch' in result.stderr
                assert not any(p.is_file() and 'runtime-binary' not in p.name for p in (Path(case[profile_key]) / '.codex').rglob('*'))
            (package / 'RUNTIME.tsv').write_text(sealed, encoding='utf-8', newline='\n')
            state['fail'] = True
            result = subprocess.run(command + ['-version'], cwd=package, env=profile('http-failure'), capture_output=True, timeout=25)
            assert result.returncode != 0 and b'download failed' in result.stderr
            before = state['requests']
            (package / 'RUNTIME.tsv').write_text(rows[0] + '\n', encoding='utf-8', newline='\n')
            result = subprocess.run(command + ['-version'], cwd=package, env=profile('missing-target'), capture_output=True, timeout=20)
            assert result.returncode != 0 and b'no sealed runtime entry' in result.stderr
            assert state['requests'] == before
            state['fail'] = False
            all_catalog = scratch / 'all-catalog'
            shutil.copytree(args.distribution / 'catalog', all_catalog)
            for manifest in all_catalog.rglob('RUNTIME.tsv'):
                rewritten = []
                for row in manifest.read_text(encoding='utf-8').splitlines():
                    fields = row.split('\t')
                    if not row.startswith('@'):
                        fields[-1] = 'https://127.0.0.1:' + str(server.server_port) + '/' + fields[-1].rsplit('/', 1)[-1]
                    rewritten.append('\t'.join(fields))
                manifest.write_text('\n'.join(rewritten) + '\n', encoding='utf-8', newline='\n')
            all_env = profile('all-connectors')
            subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/test-native-marketplace.py'),
                            '--catalog', str(all_catalog)], env=all_env, check=True, timeout=180)
            assert state['requests'] == before + 9, 'each native connector must download once for both hosts'
            billing = all_catalog / 'plugins/itecs-billing-audit'
            command_help = ['git', '-c', ALIAS, 'itecs-launch', str(billing / 'scripts/run-source-report'), 'halopsa', '-h']
            help_result = subprocess.run(command_help, cwd=billing, env=all_env, capture_output=True, timeout=30)
            assert b'-month' in help_result.stdout + help_result.stderr
            before_offline = state['requests']
            offline_billing = profile('offline-billing')
            offline_billing['AUDIT_PHASE'] = 'finalize'
            result = subprocess.run(['git', '-c', ALIAS, 'itecs-launch', str(billing / 'scripts/run-billing-audit')],
                                    cwd=billing, env=offline_billing, capture_output=True, timeout=20)
            assert result.returncode != 0 and b'offline command' in result.stderr
            assert state['requests'] == before_offline
            print(json.dumps({'result': 'passed', 'platform': platform.platform(), 'tools': len(expected),
                'cases': ['cold', 'warm', 'corrupt-cache', 'concurrent', 'offline', 'native-checksum', 'gzip-checksum', 'native-size', 'http-failure', 'missing-target', 'all-nine-connectors', 'billing-help', 'offline-finalization'],
                'vendor_calls': False, 'os_trust_modified': False}), flush=True)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
