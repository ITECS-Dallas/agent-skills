#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/install.sh [--target codex|agents|both] [--mode copy|symlink] [--force]

Defaults:
  --target both
  --mode symlink

Environment overrides:
  CODEX_HOME   default: $HOME/.codex
  AGENTS_HOME  default: $HOME/.agents
USAGE
}

target="both"
mode="symlink"
force="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      target="${2:-}"
      shift 2
      ;;
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    --force)
      force="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$target" in
  codex|agents|both) ;;
  *)
    echo "error: --target must be codex, agents, or both" >&2
    exit 2
    ;;
esac

case "$mode" in
  copy|symlink) ;;
  *)
    echo "error: --mode must be copy or symlink" >&2
    exit 2
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_root="$repo_root/plugins/portable-development-workflow/skills"

if [[ ! -d "$skills_root" ]]; then
  echo "error: skills root not found: $skills_root" >&2
  exit 1
fi

install_one_target() {
  local dest_root="$1"
  mkdir -p "$dest_root"

  local skill_dir skill_name dest
  for skill_dir in "$skills_root"/*; do
    [[ -d "$skill_dir" ]] || continue
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    skill_name="$(basename "$skill_dir")"
    dest="$dest_root/$skill_name"

    if [[ -e "$dest" || -L "$dest" ]]; then
      if [[ "$force" != "true" ]]; then
        echo "skip: $dest exists; rerun with --force to replace" >&2
        continue
      fi
      rm -rf "$dest"
    fi

    if [[ "$mode" == "symlink" ]]; then
      ln -s "$skill_dir" "$dest"
    else
      mkdir -p "$dest"
      cp -R "$skill_dir"/. "$dest"/
    fi

    echo "installed: $dest"
  done
}

if [[ "$target" == "codex" || "$target" == "both" ]]; then
  install_one_target "${CODEX_HOME:-$HOME/.codex}/skills"
fi

if [[ "$target" == "agents" || "$target" == "both" ]]; then
  install_one_target "${AGENTS_HOME:-$HOME/.agents}/skills"
fi
