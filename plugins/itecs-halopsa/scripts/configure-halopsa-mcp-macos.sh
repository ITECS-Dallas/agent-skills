#!/usr/bin/env bash
set -euo pipefail

TECHNICIAN=""
OP_COMMAND="/opt/homebrew/bin/op-itecs"
CONFIG_PATH="${HOME:?HOME is required}/.codex/halopsa-mcp/config.json"
FORCE=0
BASE_URL="https://halopsa.itecs.io/api"
TOKEN_URL="https://halopsa.itecs.io/auth/token"

usage() {
  cat <<'EOF'
Usage: configure-halopsa-mcp-macos.sh --technician "Full Name" [options]

Options:
  --technician NAME  Exact HaloPSA technician name (required)
  --op-command PATH  Prompt-free ITECS 1Password wrapper
                     (default: /opt/homebrew/bin/op-itecs)
  --config PATH      Destination config path
                     (default: ~/.codex/halopsa-mcp/config.json)
  --force            Replace an existing config after all validation passes
  --help             Show this help
EOF
}

fail() {
  printf 'HaloPSA setup failed: %s\n' "$1" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --technician)
      [[ $# -ge 2 ]] || fail "--technician requires a value"
      TECHNICIAN="$2"
      shift 2
      ;;
    --op-command)
      [[ $# -ge 2 ]] || fail "--op-command requires a value"
      OP_COMMAND="$2"
      shift 2
      ;;
    --config)
      [[ $# -ge 2 ]] || fail "--config requires a value"
      CONFIG_PATH="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[[ "$(uname -s)" == Darwin* ]] || fail "this configurator supports macOS only"
[[ -n "$TECHNICIAN" ]] || fail "--technician is required"
[[ ${#TECHNICIAN} -le 100 ]] || fail "technician name is too long"
case "$TECHNICIAN" in
  *$'\n'*|*$'\r'*|*$'\t'*|*/*|*\\*|*\"*) fail "technician name contains an unsupported character" ;;
esac
[[ "$OP_COMMAND" == /* ]] || fail "--op-command must be an absolute path"
[[ -x "$OP_COMMAND" ]] || fail "prompt-free 1Password wrapper is not executable: $OP_COMMAND"
command -v curl >/dev/null 2>&1 || fail "curl is required for OAuth validation"

if [[ -e "$CONFIG_PATH" && "$FORCE" -ne 1 ]]; then
  fail "config already exists at $CONFIG_PATH; rerun with --force to replace it"
fi

ITEM_TITLE="GO-MCP HaloPSA $TECHNICIAN Read Write"
VAULT_PREFIX="op://Automation Vault/$ITEM_TITLE"

read_op_field() {
  local field="$1"
  local value
  if ! value=$("$OP_COMMAND" read "$VAULT_PREFIX/$field" 2>/dev/null); then
    fail "Automation Vault item '$ITEM_TITLE' is missing, inaccessible, or incomplete at field $field"
  fi
  [[ -n "$value" ]] || fail "Automation Vault item '$ITEM_TITLE' has an empty $field field"
  printf '%s' "$value"
}

scope_has() {
  case " $HALO_SCOPE " in
    *" $1 "*) return 0 ;;
    *) return 1 ;;
  esac
}

url_encode() {
  local value="$1"
  local encoded=""
  local char
  local hex
  local index
  LC_ALL=C
  for ((index = 0; index < ${#value}; index++)); do
    char="${value:index:1}"
    case "$char" in
      [a-zA-Z0-9.~_-]) encoded+="$char" ;;
      *)
        printf -v hex '%%%02X' "'$char"
        encoded+="$hex"
        ;;
    esac
  done
  printf '%s' "$encoded"
}

json_string() {
  local value="$1"
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//$'\n'/\\n}
  value=${value//$'\r'/\\r}
  value=${value//$'\t'/\\t}
  printf '"%s"' "$value"
}

HALO_CLIENT_ID=$(read_op_field HALO_CLIENT_ID)
HALO_CLIENT_SECRET=$(read_op_field HALO_CLIENT_SECRET)
HALO_SCOPE=$(read_op_field HALO_SCOPE)
HALO_AGENT=$(read_op_field HALO_AGENT)
VAULT_BASE_URL=$(read_op_field HALO_BASE_URL)
VAULT_TOKEN_URL=$(read_op_field HALO_TOKEN_URL)

[[ "$HALO_AGENT" == "$TECHNICIAN" ]] || fail "HALO_AGENT does not match technician '$TECHNICIAN'"
[[ "$VAULT_BASE_URL" == "$BASE_URL" ]] || fail "HALO_BASE_URL is not the approved ITECS HaloPSA API URL"
[[ "$VAULT_TOKEN_URL" == "$TOKEN_URL" ]] || fail "HALO_TOKEN_URL is not the approved ITECS HaloPSA token URL"
scope_has read:tickets || fail "HALO_SCOPE is missing read:tickets"
scope_has edit:tickets || fail "HALO_SCOPE is missing edit:tickets"
if scope_has read:crm || scope_has read:distributionlists; then
  fail "HALO_SCOPE contains a prohibited broad read scope"
fi

OAUTH_BODY="grant_type=client_credentials&client_id=$(url_encode "$HALO_CLIENT_ID")&client_secret=$(url_encode "$HALO_CLIENT_SECRET")&scope=$(url_encode "$HALO_SCOPE")"
if ! HTTP_CODE=$(printf '%s' "$OAUTH_BODY" | curl --silent --show-error --output /dev/null --write-out '%{http_code}' --header 'Content-Type: application/x-www-form-urlencoded' --data-binary @- "$TOKEN_URL"); then
  fail "HaloPSA OAuth validation could not reach the approved token endpoint"
fi
[[ "$HTTP_CODE" == 200 ]] || fail "HaloPSA OAuth validation returned HTTP $HTTP_CODE for '$ITEM_TITLE'"

CONFIG_DIR=$(dirname "$CONFIG_PATH")
mkdir -p "$CONFIG_DIR"
umask 077
TEMP_CONFIG=$(mktemp "$CONFIG_DIR/.halopsa-config.XXXXXX")
cleanup() {
  rm -f "$TEMP_CONFIG"
}
trap cleanup EXIT

{
  printf '{\n  "servers": [\n    {\n'
  printf '      "id": "itecs-halopsa",\n'
  printf '      "name": "ITECS HaloPSA",\n'
  printf '      "base_url": "%s",\n' "$BASE_URL"
  printf '      "token_url": "%s",\n' "$TOKEN_URL"
  printf '      "client_id_command": [%s, "read", %s],\n' "$(json_string "$OP_COMMAND")" "$(json_string "$VAULT_PREFIX/HALO_CLIENT_ID")"
  printf '      "client_secret_command": [%s, "read", %s],\n' "$(json_string "$OP_COMMAND")" "$(json_string "$VAULT_PREFIX/HALO_CLIENT_SECRET")"
  printf '      "scope_command": [%s, "read", %s],\n' "$(json_string "$OP_COMMAND")" "$(json_string "$VAULT_PREFIX/HALO_SCOPE")"
  printf '      "timeout_seconds": 30,\n'
  printf '      "max_attempts": 3,\n'
  printf '      "default_page_size": 25\n'
  printf '    }\n  ]\n}\n'
} >"$TEMP_CONFIG"

chmod 600 "$TEMP_CONFIG"
if [[ -e "$CONFIG_PATH" && "$FORCE" -ne 1 ]]; then
  fail "config appeared at $CONFIG_PATH during setup; no file was replaced"
fi
mv -f "$TEMP_CONFIG" "$CONFIG_PATH"
trap - EXIT

unset HALO_CLIENT_ID HALO_CLIENT_SECRET HALO_SCOPE HALO_AGENT VAULT_BASE_URL VAULT_TOKEN_URL OAUTH_BODY
printf 'HaloPSA OAuth validated for %s.\n' "$ITEM_TITLE"
printf 'Command-backed config written to %s. Restart Codex Desktop and start a new task.\n' "$CONFIG_PATH"
