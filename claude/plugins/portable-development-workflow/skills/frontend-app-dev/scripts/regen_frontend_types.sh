#!/usr/bin/env bash
set -euo pipefail

if [[ -f package.json ]]; then
  if npm run | grep -qE 'generate|codegen|schema|types'; then
    echo "Found package scripts that may regenerate frontend types:"
    npm run | grep -E 'generate|codegen|schema|types' || true
    echo "Run the project-specific generation command documented in package.json."
    exit 0
  fi
fi

echo "No generic frontend type generation command can be inferred."
echo "Inspect local project docs and generated file headers before editing generated types."
