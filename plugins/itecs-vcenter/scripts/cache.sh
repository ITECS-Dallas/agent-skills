#!/usr/bin/env bash
# Source checkouts declare bundled mode; published thin packages declare release.
# A release package never substitutes a bundled or unverified executable.
itecs_sha256() {
  local sum
  if [[ "$ITECS_OS" == darwin ]]; then
    sum="$(/usr/bin/shasum -a 256 "$1")" || return
  else
    sum="$(sha256sum "$1")" || return
  fi
  printf '%s' "${sum%% *}"
}

itecs_binary() (
  set -euo pipefail
  umask 077
  local relative="$1" mode
  fail() { printf 'ITECS runtime: %s\n' "$1" >&2; exit 2; }
  [[ "$relative" == bin/* && "$relative" != *..* && "$relative" != *//* && "$relative" != *\\* ]] || fail 'invalid binary path'
  mode="$(cat "$ITECS_PLUGIN_DIR/runtime-mode")" || fail 'runtime-mode is missing; reinstall the package'
  if [[ "$mode" == bundled ]]; then
    [[ -f "$ITECS_PLUGIN_DIR/$relative" ]] || fail "bundled binary is missing: $relative"
    printf '%s\n' "$ITECS_PLUGIN_DIR/$relative"
    exit 0
  fi
  [[ "$mode" == release ]] || fail 'unrecognized runtime-mode; reinstall the package'
  [[ -n "$ITECS_USER_DIR" ]] || fail 'the host user profile is unavailable'
  local path sha compressed_sha bytes compressed_bytes url extra package='' version='' found=0
  local wanted_sha='' wanted_compressed_sha='' wanted_bytes='' wanted_compressed_bytes='' wanted_url=''
  while IFS=$'\t' read -r path sha compressed_sha bytes compressed_bytes url extra; do
    if [[ "$path" == @package ]]; then
      [[ -z "$package" ]] || fail 'duplicate package identity'
      package="$sha"; version="$compressed_sha"
    elif [[ "$path" == "$relative" ]]; then
      [[ "$found" == 0 && -z "$extra" ]] || fail 'duplicate or malformed binary entry'
      found=1
      wanted_sha="$sha"; wanted_compressed_sha="$compressed_sha"; wanted_bytes="$bytes"
      wanted_compressed_bytes="$compressed_bytes"; wanted_url="$url"
    fi
  done < "$ITECS_PLUGIN_DIR/RUNTIME.tsv"
  [[ "$package" =~ ^[a-z][a-z0-9-]+$ && "$version" =~ ^[A-Za-z0-9.+-]+$ && "$found" == 1 ]] || fail "no sealed runtime entry for $relative"
  [[ "$wanted_sha" =~ ^[a-f0-9]{64}$ && "$wanted_compressed_sha" =~ ^[a-f0-9]{64}$ ]] || fail 'invalid runtime checksum'
  [[ "$wanted_bytes" =~ ^[1-9][0-9]*$ && "$wanted_compressed_bytes" =~ ^[1-9][0-9]*$ && "$wanted_url" == https://* ]] || fail 'invalid runtime size or HTTPS URL'
  local target="$ITECS_USER_DIR/.codex/itecs-runtime/$package/$version/$relative"
  if [[ -e "$target" ]]; then
    [[ -f "$target" && "$(itecs_sha256 "$target")" == "$wanted_sha" ]] || fail "cached binary checksum mismatch; remove only $target and prepare it again"
    printf '%s\n' "$target"
    exit 0
  fi
  [[ "${ITECS_RUNTIME_OFFLINE:-0}" != 1 ]] || fail 'this offline command requires a prepared runtime; run scripts/prepare-runtime before going offline'
  mkdir -p "$(dirname "$target")"
  # EXIT traps in macOS Bash 3.2 run after function-local variables unwind.
  # These cleanup paths belong to this subshell, not the parent launcher.
  lock="$target.lock"
  local count=0
  until mkdir "$lock" 2>/dev/null; do
    if [[ -f "$target" && "$(itecs_sha256 "$target")" == "$wanted_sha" ]]; then
      printf '%s\n' "$target"; exit 0
    fi
    ((count+=1))
    [[ "$count" -lt 200 ]] || fail "runtime preparation is locked at $lock; check the preparing process before removing a stale lock"
    sleep 0.1
  done
  compressed='' temporary=''
  cleanup() { rm -f -- "$compressed" "$temporary"; rmdir -- "$lock"; }
  trap cleanup EXIT
  # Another launcher may have published between the initial check and the lock.
  if [[ -e "$target" ]]; then
    [[ -f "$target" && "$(itecs_sha256 "$target")" == "$wanted_sha" ]] || fail 'cached binary changed during preparation'
    printf '%s\n' "$target"; exit 0
  fi
  compressed="$(mktemp "$(dirname "$target")/.runtime-gzip.XXXXXX")"
  temporary="$(mktemp "$(dirname "$target")/.runtime-binary.XXXXXX")"
  printf 'ITECS runtime: preparing %s %s (%s)\n' "$package" "$version" "$ITECS_PLATFORM" >&2
  curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
    --connect-timeout 5 --max-time 15 --max-filesize "$wanted_compressed_bytes" \
    --output "$compressed" "$wanted_url" || fail 'release download failed; check connectivity and run scripts/prepare-runtime before restarting the host'
  [[ "$(itecs_sha256 "$compressed")" == "$wanted_compressed_sha" ]] || fail 'downloaded release checksum mismatch; no executable was installed'
  gzip -dc "$compressed" > "$temporary" || fail 'release decompression failed'
  [[ "$(wc -c < "$temporary" | tr -d '[:space:]')" == "$wanted_bytes" && "$(itecs_sha256 "$temporary")" == "$wanted_sha" ]] || fail 'executable size or checksum mismatch; no executable was installed'
  chmod 700 "$temporary"
  mv -- "$temporary" "$target"
  printf '%s\n' "$target"
)

itecs_binary_dir() (
  set -euo pipefail
  local platform="$1" mode path sha rest resolved='' directory=''
  mode="$(cat "$ITECS_PLUGIN_DIR/runtime-mode")"
  if [[ "$mode" == bundled ]]; then
    printf '%s\n' "$ITECS_PLUGIN_DIR/bin/$platform"; exit 0
  fi
  while IFS=$'\t' read -r path sha rest; do
    if [[ "$path" == "bin/$platform/"* ]]; then
      resolved="$(itecs_binary "$path")"
      directory="$(dirname "$resolved")"
    fi
  done < "$ITECS_PLUGIN_DIR/RUNTIME.tsv"
  [[ -n "$directory" ]] || { printf 'ITECS runtime: no binaries for %s\n' "$platform" >&2; exit 2; }
  printf '%s\n' "$directory"
)
