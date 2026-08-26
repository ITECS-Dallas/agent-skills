#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
CONFIGURATOR="$ROOT/scripts/configure-halopsa-mcp-macos.sh"
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/halopsa-config-test.XXXXXX")
cleanup() {
  rm -rf "$TEST_ROOT"
}
trap cleanup EXIT

FAKE_BIN="$TEST_ROOT/bin"
mkdir -p "$FAKE_BIN"

cat >"$FAKE_BIN/op-itecs" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
[[ "$1" == read ]]
case "$2" in
  */HALO_CLIENT_ID) printf 'test-client-id' ;;
  */HALO_CLIENT_SECRET) printf 'test-client-secret' ;;
  */HALO_SCOPE) printf '%s' "${TEST_HALO_SCOPE:-read:tickets edit:tickets}" ;;
  */HALO_AGENT) printf '%s' "${TEST_HALO_AGENT:-Daniel Moran}" ;;
  */HALO_BASE_URL) printf 'https://halopsa.itecs.io/api' ;;
  */HALO_TOKEN_URL) printf 'https://halopsa.itecs.io/auth/token' ;;
  *) exit 1 ;;
esac
EOF

cat >"$FAKE_BIN/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
while IFS= read -r _; do :; done
printf '%s' "${TEST_HTTP_CODE:-200}"
EOF
chmod +x "$FAKE_BIN/op-itecs" "$FAKE_BIN/curl"

CONFIG_PATH="$TEST_ROOT/config.json"
PATH="$FAKE_BIN:$PATH" "$CONFIGURATOR" \
  --technician "Daniel Moran" \
  --op-command "$FAKE_BIN/op-itecs" \
  --config "$CONFIG_PATH" >/dev/null

node - "$CONFIG_PATH" "$FAKE_BIN/op-itecs" <<'EOF'
const fs = require('fs');
const [configPath, opPath] = process.argv.slice(2);
const raw = fs.readFileSync(configPath, 'utf8');
const config = JSON.parse(raw);
const server = config.servers?.[0];
if (!server) throw new Error('missing server config');
const prefix = 'op://Automation Vault/GO-MCP HaloPSA Daniel Moran Read Write';
const expected = {
  client_id_command: [opPath, 'read', `${prefix}/HALO_CLIENT_ID`],
  client_secret_command: [opPath, 'read', `${prefix}/HALO_CLIENT_SECRET`],
  scope_command: [opPath, 'read', `${prefix}/HALO_SCOPE`]
};
for (const [key, value] of Object.entries(expected)) {
  if (JSON.stringify(server[key]) !== JSON.stringify(value)) {
    throw new Error(`${key} does not match the command-backed reference`);
  }
}
if (raw.includes('test-client-id') || raw.includes('test-client-secret')) {
  throw new Error('config contains a resolved credential');
}
if (server.base_url !== 'https://halopsa.itecs.io/api' || server.token_url !== 'https://halopsa.itecs.io/auth/token') {
  throw new Error('config contains an unexpected HaloPSA endpoint');
}
EOF

[[ "$(stat -f '%Lp' "$CONFIG_PATH")" == 600 ]] || { printf 'config mode is not 600\n' >&2; exit 1; }

if PATH="$FAKE_BIN:$PATH" "$CONFIGURATOR" --technician "Daniel Moran" --op-command "$FAKE_BIN/op-itecs" --config "$CONFIG_PATH" >/dev/null 2>&1; then
  printf 'expected existing config protection to fail\n' >&2
  exit 1
fi

PATH="$FAKE_BIN:$PATH" "$CONFIGURATOR" --technician "Daniel Moran" --op-command "$FAKE_BIN/op-itecs" --config "$CONFIG_PATH" --force >/dev/null

MISMATCH_CONFIG="$TEST_ROOT/mismatch.json"
if TEST_HALO_AGENT="Another Technician" PATH="$FAKE_BIN:$PATH" "$CONFIGURATOR" --technician "Daniel Moran" --op-command "$FAKE_BIN/op-itecs" --config "$MISMATCH_CONFIG" >/dev/null 2>&1; then
  printf 'expected HALO_AGENT mismatch to fail\n' >&2
  exit 1
fi
[[ ! -e "$MISMATCH_CONFIG" ]] || { printf 'mismatch config was written\n' >&2; exit 1; }

SCOPE_CONFIG="$TEST_ROOT/scope.json"
if TEST_HALO_SCOPE="read:tickets edit:tickets read:crm" PATH="$FAKE_BIN:$PATH" "$CONFIGURATOR" --technician "Daniel Moran" --op-command "$FAKE_BIN/op-itecs" --config "$SCOPE_CONFIG" >/dev/null 2>&1; then
  printf 'expected prohibited scope to fail\n' >&2
  exit 1
fi
[[ ! -e "$SCOPE_CONFIG" ]] || { printf 'scope config was written\n' >&2; exit 1; }

OAUTH_CONFIG="$TEST_ROOT/oauth.json"
if TEST_HTTP_CODE=401 PATH="$FAKE_BIN:$PATH" "$CONFIGURATOR" --technician "Daniel Moran" --op-command "$FAKE_BIN/op-itecs" --config "$OAUTH_CONFIG" >/dev/null 2>&1; then
  printf 'expected OAuth rejection to fail\n' >&2
  exit 1
fi
[[ ! -e "$OAUTH_CONFIG" ]] || { printf 'OAuth failure config was written\n' >&2; exit 1; }

printf 'macOS HaloPSA configurator tests passed\n'
