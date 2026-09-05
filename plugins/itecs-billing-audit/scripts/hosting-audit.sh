#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Hosting is a selected-source view of the consolidated billing workflow. Keep
# one reconciliation engine so monthly hosting and full billing audits cannot
# drift into different quantity decisions.
export SOURCES="vcenter"
export AUDIT_PHASE="${AUDIT_PHASE:-full}"
exec "$ROOT_DIR/scripts/billing-audit.sh"
