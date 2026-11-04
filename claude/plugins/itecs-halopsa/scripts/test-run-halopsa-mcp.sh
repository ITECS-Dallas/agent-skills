#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
LAUNCHER="$ROOT/scripts/run-halopsa-mcp"
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/halopsa-launcher-test.XXXXXX")
cleanup() {
  rm -rf "$TEST_ROOT"
}
trap cleanup EXIT

FAKE_BIN="$TEST_ROOT/bin"
mkdir -p "$FAKE_BIN"

cat >"$FAKE_BIN/uname" <<'EOF'
#!/usr/bin/env bash
case "$1" in
  -s) printf 'MINGW64_NT-10.0' ;;
  -m) printf 'x86_64' ;;
  *) exit 2 ;;
esac
EOF

cat >"$FAKE_BIN/cygpath" <<'EOF'
#!/usr/bin/env bash
[[ "$1" == -m ]]
printf 'C:/%s/Technician' 'Users'
EOF
chmod +x "$FAKE_BIN/uname" "$FAKE_BIN/cygpath"

ERROR_FILE="$TEST_ROOT/error.txt"
if USERPROFILE='C:\Users\Technician' PATH="$FAKE_BIN:$PATH" "$LAUNCHER" 2>"$ERROR_FILE"; then
  printf 'expected missing Windows config to fail\n' >&2
  exit 1
fi
WINDOWS_USER_DIR='Users'
if ! grep -Fq "C:/$WINDOWS_USER_DIR/Technician/.codex/halopsa-mcp/config.json" "$ERROR_FILE"; then
  printf 'launcher did not resolve the Windows config from USERPROFILE\n' >&2
  exit 1
fi

if PATH="$FAKE_BIN:$PATH" env -u USERPROFILE "$LAUNCHER" 2>"$ERROR_FILE"; then
  printf 'expected missing USERPROFILE to fail\n' >&2
  exit 1
fi
if ! grep -Fq 'USERPROFILE is required on Windows' "$ERROR_FILE"; then
  printf 'launcher did not fail closed without USERPROFILE\n' >&2
  exit 1
fi

printf 'HaloPSA launcher path tests passed\n'
