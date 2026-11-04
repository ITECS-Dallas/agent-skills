#!/usr/bin/env bash
# First-start ITECS setup. This script never reads or stores a credential value.
set -euo pipefail
umask 077
config_path="${1:?config path is required}"
platform="${2:?platform is required}"
fail() { printf 'N-central automatic setup failed: %s\n' "$1" >&2; exit 2; }
# An existing config, including a dangling symlink, belongs to its operator.
[[ ! -e "$config_path" && ! -L "$config_path" ]] || exit 0
case "$platform" in
  darwin) wrapper=/opt/homebrew/bin/op-itecs ;;
  linux|windows) wrapper="$(type -P op-itecs || true)" ;;
  *) fail "unsupported platform: $platform" ;;
esac
[[ -n "$wrapper" && "$wrapper" == /* && -x "$wrapper" ]] || fail 'the approved op-itecs executable must be installed (macOS: /opt/homebrew/bin/op-itecs; Linux/Windows: on PATH). No other credential source will be used.'
if [[ "$platform" == windows ]]; then
  wrapper="$(cygpath -m "$wrapper")"
fi
# JSON strings support Unicode, spaces, quotes and backslashes. Reject control
# characters in executable paths rather than writing an invalid configuration.
[[ "$wrapper" != *[[:cntrl:]]* ]] || fail 'op-itecs path contains a control character'
wrapper="${wrapper//\\/\\\\}"
wrapper="${wrapper//\"/\\\"}"
config_dir="$(dirname "$config_path")"
mkdir -p "$config_dir"
temporary="$(mktemp "$config_dir/.ncentral-config.XXXXXX")"
trap 'rm -f "$temporary"' EXIT
printf '{"servers":[{"id":"itecs","name":"ITECS N-central","base_url":"https://manage.itecsonline.com","jwt_command":["%s","read","op://Automation Vault/h6b4ek24qjuqdjjrvrtagfsnme/credential"],"timeout_seconds":30}]}\n' "$wrapper" > "$temporary"
# Publish without replacing a config another concurrent launch may have made.
if ln "$temporary" "$config_path" 2>/dev/null; then
  printf 'N-central configured with the ITECS Automation Vault API reader.\n' >&2
elif [[ ! -f "$config_path" ]]; then
  fail 'could not create runtime configuration'
fi
