#!/usr/bin/env bash
# shellcheck disable=SC2034 # Globals are consumed by the sourcing launchers.
# Shared implementation copied into each self-contained plugin at build time.
itecs_platform() {
  local os_name arch_name
  os_name="$(uname -s)"
  arch_name="$(uname -m)"
  case "$os_name" in
    Darwin*) ITECS_OS=darwin ;;
    MINGW*|MSYS*|CYGWIN*) ITECS_OS=windows ;;
    *) printf 'No bundled binary for platform %s.\n' "$os_name" >&2; return 2 ;;
  esac
  case "$arch_name" in
    arm64|aarch64) ITECS_ARCH=arm64 ;;
    x86_64|amd64) ITECS_ARCH=amd64 ;;
    *) printf 'No bundled binary for architecture %s.\n' "$arch_name" >&2; return 2 ;;
  esac
  ITECS_SUFFIX=""
  ITECS_USER_DIR="${HOME:-}"
  if [[ "$ITECS_OS" == windows ]]; then
    ITECS_SUFFIX=.exe
    [[ -n "${USERPROFILE:-}" ]] || { printf 'USERPROFILE is required on Windows.\n' >&2; return 2; }
    ITECS_USER_DIR="$(cygpath -m "$USERPROFILE")"
  fi
  ITECS_PLATFORM="$ITECS_OS-$ITECS_ARCH"
}

itecs_config() {
  local connector="$1" override="$2"
  ITECS_CONFIG="${!override:-$ITECS_USER_DIR/.codex/$connector-mcp/config.json}"
}
