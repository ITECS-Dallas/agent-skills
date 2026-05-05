#!/usr/bin/env bash
set -euo pipefail

if [[ -f Makefile ]] && make -qp 2>/dev/null | grep -qE '^(generate|codegen|openapi|schema|proto):'; then
  echo "Found Makefile generation targets:"
  make -qp 2>/dev/null | awk -F: '/^(generate|codegen|openapi|schema|proto):/ {print "- make " $1}' | sort -u
  exit 0
fi

if [[ -f package.json ]] && npm run | grep -qE 'generate|codegen|openapi|schema|proto'; then
  echo "Found package scripts that may regenerate backend contracts:"
  npm run | grep -E 'generate|codegen|openapi|schema|proto' || true
  exit 0
fi

echo "No generic backend generation command can be inferred."
echo "Inspect local project docs, Makefile, package scripts, and generated file headers."
