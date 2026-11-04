#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -d /opt/homebrew/bin ]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi

RUN_DATE="$(date +%Y-%m-%d)"
MONTH="${MONTH:-$(date +%Y-%m)}"
SOURCES="${SOURCES:-all}"
AUDIT_PHASE="${AUDIT_PHASE:-full}"
DRY_RUN="${DRY_RUN:-0}"
SOURCE_WORKBOOKS="${SOURCE_WORKBOOKS:-0}"
SOURCE_RUN_ID="${SOURCE_RUN_ID:-}"
RECONCILIATION_ID="${RECONCILIATION_ID:-}"
GO_BIN="${GO_BIN:-go}"
MV_BIN="${MV_BIN:-mv}"
LOCK_MKDIR_BIN="${LOCK_MKDIR_BIN:-mkdir}"
LOCK_OWNER_RM_BIN="${LOCK_OWNER_RM_BIN:-rm}"
SOURCE_OUTPUT_ARGS=()
PUBLICATION_ARTIFACT_NAMES=()
CHECKPOINT_ACCOUNTS_EXPORT_RAW="${CHECKPOINT_ACCOUNTS_EXPORT:-}"
CHECKPOINT_ACCOUNTS_EXPORT_PATH=""
SERVICE_LINE_MAPPING_RAW="${SERVICE_LINE_MAPPING:-}"
CLIENT_CROSSWALK_RAW="${CLIENT_CROSSWALK:-}"
CHECKPOINT_EXPORT_ARGS=()
STAGING_DIR=""
SOURCE_RUN_DIR=""
SOURCE_DIR=""
ATTEMPT_DIR=""
PUBLICATION_ROLLBACK_FAILED=0
AUDIT_LOCK_DIR=""
AUDIT_LOCK_HELD=0
AUDIT_LOCK_TOKEN=""
AUDIT_PENDING_SIGNAL=""

expand_path() {
  local path="$1"
  local home_prefix=$'\x7e/'
  if [ "$path" = "~" ]; then
    printf '%s\n' "$HOME"
    return
  fi
  if [[ "$path" == "$home_prefix"* ]]; then
    printf '%s/%s\n' "$HOME" "${path:2}"
    return
  fi
  if [[ "$path" == /* ]]; then
    printf '%s\n' "$path"
    return
  fi
  printf '%s/%s\n' "$ROOT_DIR" "$path"
}

is_dry_run() {
  [ "$DRY_RUN" = "1" ] || [ "$DRY_RUN" = "true" ] || [ "$DRY_RUN" = "TRUE" ]
}

source_workbooks_enabled() {
  [ "$SOURCE_WORKBOOKS" = "1" ] || [ "$SOURCE_WORKBOOKS" = "true" ] || [ "$SOURCE_WORKBOOKS" = "TRUE" ]
}

require_file() {
  if [ ! -f "$1" ]; then
    if is_dry_run; then
      printf 'DRY RUN: required file not found yet: %s\n' "$1" >&2
      return
    fi
    printf 'Required file not found: %s\n' "$1" >&2
    exit 1
  fi
}

validate_month() {
  case "$MONTH" in
    [0-9][0-9][0-9][0-9]-0[1-9]|[0-9][0-9][0-9][0-9]-1[0-2]) return ;;
    *)
      printf 'MONTH must use YYYY-MM format: %s\n' "$MONTH" >&2
      exit 1
      ;;
  esac
}

validate_identifier() {
  local name="$1"
  local value="$2"
  case "$value" in
    ""|[!A-Za-z0-9]*|*[!A-Za-z0-9._-]*)
      printf '%s must start with a letter or number and may then contain only letters, numbers, dot, underscore, and dash: %s\n' "$name" "$value" >&2
      exit 1
      ;;
  esac
  if [ "${#value}" -gt 80 ]; then
    printf '%s must be 80 characters or fewer.\n' "$name" >&2
    exit 1
  fi
}

validate_audit_phase() {
  case "$AUDIT_PHASE" in
    collect|mapping-review|finalize|full) return ;;
    *)
      printf 'AUDIT_PHASE must be collect, mapping-review, finalize, or full: %s\n' "$AUDIT_PHASE" >&2
      exit 1
      ;;
  esac
}

phase_collects_sources() {
  [ "$AUDIT_PHASE" = "collect" ] || [ "$AUDIT_PHASE" = "full" ]
}

phase_builds_mapping_review() {
  [ "$AUDIT_PHASE" = "mapping-review" ] || [ "$AUDIT_PHASE" = "full" ]
}

phase_finalizes() {
  [ "$AUDIT_PHASE" = "finalize" ] || [ "$AUDIT_PHASE" = "full" ]
}

validate_boolean() {
  local name="$1"
  local value="$2"
  case "$value" in
    0|1|true|false|TRUE|FALSE) return ;;
    *)
      printf '%s must be 0, 1, true, or false: %s\n' "$name" "$value" >&2
      exit 1
      ;;
  esac
}

canonicalize_reports_dir() {
  local path="$1"
  local parent
  local parent_canonical

  if [ -d "$path" ]; then
    (cd "$path" && pwd -P)
    return
  fi
  parent="$(dirname "$path")"
  if [ -d "$parent" ]; then
    parent_canonical="$(cd "$parent" && pwd -P)"
    printf '%s/%s\n' "$parent_canonical" "$(basename "$path")"
    return
  fi
  printf '%s\n' "$path"
}

validate_reports_dir() {
  local path="$1"
  case "$path" in
    /|"$HOME"|"$ROOT_DIR"|*"/../"*|*"/.."|*"/./"*|*"/.")
      printf 'REPORTS_DIR must be a dedicated report directory, not a broad or unresolved path: %s\n' "$path" >&2
      exit 1
      ;;
  esac
}

normalize_sources() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -e 's/[[:space:]]\{1,\}/,/g' -e 's/,,*/,/g' -e 's/^,//' -e 's/,$//'
}

validate_sources() {
  local normalized_sources="$1"
  local source
  local seen_all=0
  local seen_sources=','

  if [ -z "$normalized_sources" ]; then
    printf 'SOURCES must select at least one supported source.\n' >&2
    exit 1
  fi

  IFS=',' read -r -a requested_sources <<< "$normalized_sources"
  for source in "${requested_sources[@]}"; do
    case "$seen_sources" in
      *",$source,"*)
        printf 'Duplicate billing source: %s\n' "$source" >&2
        exit 1
        ;;
    esac
    seen_sources="${seen_sources}${source},"
    case "$source" in
      all) seen_all=1 ;;
      vcenter|pax8|sophos|checkpoint|veeam) ;;
      *)
        printf 'Unsupported billing source: %s\n' "$source" >&2
        exit 1
        ;;
    esac
  done

  if [ "$seen_all" -eq 1 ] && [ "${#requested_sources[@]}" -ne 1 ]; then
    printf 'SOURCES=all cannot be combined with individual sources.\n' >&2
    exit 1
  fi
}

source_enabled() {
  local source="$1"
  case ",$ENABLED_SOURCES," in
    *",all,"*|*",$source,"*) return 0 ;;
    *) return 1 ;;
  esac
}

run_in_dir() {
  local title="$1"
  local dir="$2"
  shift 2

  # Installed packages supply the same commands as compiled executables.
  # Source checkouts continue to use GO_BIN and go run when this is unset.
  if [ -n "${BILLING_AUDIT_BIN_DIR:-}" ]; then
    local executable
    if [ "$3" = "./cmd/reconcile" ]; then
      executable="$BILLING_AUDIT_BIN_DIR/billing-reconcile"
    else
      executable="$BILLING_AUDIT_BIN_DIR/${dir##*/}-billing-report"
    fi
    case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) executable="$executable.exe" ;; esac
    shift 3
    set -- "$executable" "$@"
    dir="$ROOT_DIR"
  fi

  printf '\n==> %s\n' "$title"
  if is_dry_run; then
    printf 'DRY RUN: cd %q &&' "$dir"
    local arg
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
    return
  fi
  (
    cd "$dir"
    "$@"
  )
}

copy_required_file() {
  local source_path="$1"
  local destination_path="$2"
  require_file "$source_path"
  if is_dry_run; then
    printf 'DRY RUN: copy %q to %q\n' "$source_path" "$destination_path"
    return
  fi
  cp "$source_path" "$destination_path"
  chmod 600 "$destination_path"
}

require_run_directory() {
  local path="$1"
  if [ ! -d "$path" ] || [ -L "$path" ]; then
    if is_dry_run; then
      printf 'DRY RUN: required run directory not found yet: %s\n' "$path" >&2
      return
    fi
    printf 'Required run directory is missing or is not a real directory: %s\n' "$path" >&2
    exit 1
  fi
}

commit_staged_directory() {
  local staged_path="$1"
  local final_path="$2"

  if [ -e "$final_path" ] || [ -L "$final_path" ]; then
    printf 'Immutable billing run destination already exists; refusing to overwrite it: %s\n' "$final_path" >&2
    return 1
  fi
  if ! "$MV_BIN" -- "$staged_path" "$final_path"; then
    printf 'Could not commit immutable billing run directory: %s\n' "$final_path" >&2
    return 1
  fi
  STAGING_DIR=""
}

secure_artifact_tree() {
  local directory="$1"
  local artifact

  for artifact in "$directory"/* "$directory"/inputs/*; do
    if [ -f "$artifact" ] && [ ! -L "$artifact" ]; then
      chmod 600 "$artifact"
    fi
  done
}

acquire_audit_lock() {
  local lock_cleanup_failed

  AUDIT_LOCK_DIR="$REPORTS_DIR/.billing-audit.lock"
  AUDIT_LOCK_TOKEN="$SOURCE_RUN_ID:${RECONCILIATION_ID:-none}:$$"
  AUDIT_PENDING_SIGNAL=""
  trap handle_audit_exit EXIT
  trap 'AUDIT_PENDING_SIGNAL=INT' INT
  trap 'AUDIT_PENDING_SIGNAL=TERM' TERM
  if ! "$LOCK_MKDIR_BIN" "$AUDIT_LOCK_DIR"; then
    trap - INT TERM
    trap - EXIT
    printf 'Another billing audit may be active, or a stale lock requires review: %s\n' "$AUDIT_LOCK_DIR" >&2
    exit_after_lock_acquisition_failure
  fi
  if ! (umask 077 && printf '%s\n' "$AUDIT_LOCK_TOKEN" > "$AUDIT_LOCK_DIR/owner"); then
    lock_cleanup_failed=0
    if [ -f "$AUDIT_LOCK_DIR/owner" ] && [ ! -L "$AUDIT_LOCK_DIR/owner" ]; then
      rm -f -- "$AUDIT_LOCK_DIR/owner" || lock_cleanup_failed=1
    fi
    rmdir "$AUDIT_LOCK_DIR" 2>/dev/null || lock_cleanup_failed=1
    trap - INT TERM
    trap - EXIT
    printf 'Could not write billing audit lock owner metadata: %s\n' "$AUDIT_LOCK_DIR/owner" >&2
    if [ "$lock_cleanup_failed" -eq 1 ]; then
      printf 'The partially acquired audit lock was retained because its contents could not be safely cleaned up; inspect it before removal: %s\n' "$AUDIT_LOCK_DIR" >&2
    fi
    exit_after_lock_acquisition_failure
  fi
  AUDIT_LOCK_HELD=1
  trap - INT TERM
  case "$AUDIT_PENDING_SIGNAL" in
    INT) exit 130 ;;
    TERM) exit 143 ;;
  esac
}

release_audit_lock() {
  local lock_owner_file
  local observed_token
  local previous_int_trap
  local previous_term_trap
  local release_status=0

  if [ "$AUDIT_LOCK_HELD" -ne 1 ]; then
    return
  fi
  lock_owner_file="$AUDIT_LOCK_DIR/owner"
  if [ ! -f "$lock_owner_file" ]; then
    printf 'Could not release billing audit lock because its owner metadata is missing; verify ownership before removal: %s\n' "$AUDIT_LOCK_DIR" >&2
    return 1
  fi
  observed_token="$(<"$lock_owner_file")"
  if [ "$observed_token" != "$AUDIT_LOCK_TOKEN" ]; then
    printf 'Could not release billing audit lock because its owner metadata changed; another process may own it: %s\n' "$AUDIT_LOCK_DIR" >&2
    return 1
  fi
  previous_int_trap="$(trap -p INT)"
  previous_term_trap="$(trap -p TERM)"
  AUDIT_PENDING_SIGNAL=""
  trap 'AUDIT_PENDING_SIGNAL=INT' INT
  trap 'AUDIT_PENDING_SIGNAL=TERM' TERM
  if ! "$LOCK_OWNER_RM_BIN" -f -- "$lock_owner_file"; then
    printf 'Could not remove billing audit lock owner metadata: %s\n' "$lock_owner_file" >&2
    release_status=1
  elif ! rmdir "$AUDIT_LOCK_DIR"; then
    (umask 077 && printf '%s\n' "$AUDIT_LOCK_TOKEN" > "$lock_owner_file") || true
    printf 'Could not release billing audit lock; inspect its contents and remove the lock directory only after verifying no audit is active: %s\n' "$AUDIT_LOCK_DIR" >&2
    release_status=1
  else
    AUDIT_LOCK_HELD=0
  fi
  if [ -n "$previous_int_trap" ]; then
    eval "$previous_int_trap"
  else
    trap - INT
  fi
  if [ -n "$previous_term_trap" ]; then
    eval "$previous_term_trap"
  else
    trap - TERM
  fi
  case "$AUDIT_PENDING_SIGNAL" in
    INT) kill -INT "$$" ;;
    TERM) kill -TERM "$$" ;;
  esac
  return "$release_status"
}

handle_audit_exit() {
  local exit_status="$?"
  if [ "$exit_status" -ne 0 ] && [ -n "$STAGING_DIR" ] && [ -d "$STAGING_DIR" ]; then
    if [ "$PUBLICATION_ROLLBACK_FAILED" -eq 1 ]; then
      printf '\nBilling audit publication and rollback both failed; do not use the published report set until it is manually restored from the retained backup/staging directories.\n' >&2
    else
      printf '\nBilling audit failed before a complete publication; prior artifacts were retained or restored.\n' >&2
    fi
    printf 'Staged diagnostic artifacts were retained at: %s\n' "$STAGING_DIR" >&2
  fi
  if ! release_audit_lock; then
    : # Preserve the original failing command status; release_audit_lock reports its own diagnostic.
  fi
  return "$exit_status"
}

exit_after_lock_acquisition_failure() {
  case "$AUDIT_PENDING_SIGNAL" in
    INT) exit 130 ;;
    TERM) exit 143 ;;
    *) exit 1 ;;
  esac
}

validate_source_artifacts() {
  local source_dir="$1"
  local artifact_name
  local -a required_artifacts=(
    "halopsa-recurring-invoices-$MONTH.json"
    "halopsa-client-snapshot.json"
    "source-manifest.json"
  )

  if source_workbooks_enabled; then
    required_artifacts+=("halopsa-recurring-invoices-$MONTH.xlsx")
  fi
  if source_enabled "vcenter"; then
    required_artifacts+=("vcenter-billing-audit-$MONTH.json")
    if source_workbooks_enabled; then
      required_artifacts+=("vcenter-billing-audit-$MONTH.xlsx")
    fi
  fi
  if source_enabled "pax8"; then
    required_artifacts+=("pax8-subscriptions-$MONTH.json")
    if source_workbooks_enabled; then
      required_artifacts+=("pax8-subscriptions-$MONTH.xlsx")
    fi
  fi
  if source_enabled "sophos"; then
    required_artifacts+=("sophos-billing-usage-$MONTH.json")
    if source_workbooks_enabled; then
      required_artifacts+=("sophos-billing-usage-$MONTH.xlsx")
    fi
  fi
  if source_enabled "checkpoint"; then
    required_artifacts+=("checkpoint-harmony-usage-$MONTH.json")
    if source_workbooks_enabled; then
      required_artifacts+=("checkpoint-harmony-usage-$MONTH.xlsx")
    fi
  fi
  if source_enabled "veeam"; then
    required_artifacts+=("veeam-cloud-connect-usage-$MONTH.json")
    if source_workbooks_enabled; then
      required_artifacts+=("veeam-cloud-connect-usage-$MONTH.xlsx")
    fi
  fi

  for artifact_name in "${required_artifacts[@]}"; do
    if [ ! -s "$source_dir/$artifact_name" ]; then
      printf 'Required source-run artifact is missing or empty: %s\n' "$source_dir/$artifact_name" >&2
      return 1
    fi
  done
}

validate_mapping_review_artifacts() {
  local attempt_dir="$1"
  local artifact_name
  local -a required_artifacts=(
    "inputs/billing-client-crosswalk.json"
    "inputs/billing-service-line-mapping.json"
    "billing-client-resolution.json"
  )

  for artifact_name in "${required_artifacts[@]}"; do
    if [ ! -s "$attempt_dir/$artifact_name" ]; then
      printf 'Required mapping-review artifact is missing or empty: %s\n' "$attempt_dir/$artifact_name" >&2
      return 1
    fi
  done
}

validate_finalized_artifacts() {
  local attempt_dir="$1"
  local artifact_name
  local -a required_artifacts=(
    "billing-source-facts.json"
    "billing-reconciliation.json"
    "billing-reconciliation.xlsx"
    "reconciliation-manifest.json"
  )

  validate_mapping_review_artifacts "$attempt_dir"
  for artifact_name in "${required_artifacts[@]}"; do
    if [ ! -s "$attempt_dir/$artifact_name" ]; then
      printf 'Required finalized reconciliation artifact is missing or empty: %s\n' "$attempt_dir/$artifact_name" >&2
      return 1
    fi
  done
}

rollback_staged_publication() {
  local rollback_limit="$1"
  local rollback_index
  local rollback_target

  for ((rollback_index = 0; rollback_index <= rollback_limit; rollback_index++)); do
    rollback_target="$REPORTS_DIR/${artifact_names[$rollback_index]}"
    if [ -f "${artifact_paths[$rollback_index]}" ]; then
      continue
    fi
    if [ ! -f "$rollback_target" ]; then
      printf 'Rollback could not find promoted artifact: %s\n' "$rollback_target" >&2
      PUBLICATION_ROLLBACK_FAILED=1
      continue
    fi
    if ! "$MV_BIN" -f -- "$rollback_target" "${artifact_paths[$rollback_index]}"; then
      printf 'Rollback could not return new artifact to staging: %s\n' "$rollback_target" >&2
      PUBLICATION_ROLLBACK_FAILED=1
      continue
    fi
    if [ "${prior_exists[$rollback_index]}" = "1" ] && ! "$MV_BIN" -f -- "$backup_dir/${artifact_names[$rollback_index]}" "$rollback_target"; then
      printf 'Rollback could not restore prior artifact: %s\n' "$rollback_target" >&2
      PUBLICATION_ROLLBACK_FAILED=1
    fi
  done
}

handle_publication_signal() {
  local signal_name="$1"
  local exit_status=130

  trap '' INT TERM
  printf 'Billing artifact publication interrupted by %s; restoring the prior published set.\n' "$signal_name" >&2
  rollback_staged_publication "$rollback_limit"
  if [ "$signal_name" = "TERM" ]; then
    exit_status=143
  fi
  exit "$exit_status"
}

publish_staged_artifacts() {
  local backup_artifact
  local backup_dir
  local index
  local name
  local rollback_limit=-1
  local target
  local -a artifact_paths=()
  local -a artifact_names=()
  local -a prior_exists=()

  if [ "$#" -eq 0 ]; then
    printf 'No billing artifacts were allowlisted for publication; refusing to publish.\n' >&2
    return 1
  fi
  for name in "$@"; do
    case "$name" in
      ""|*/*|.|..)
        printf 'Invalid billing artifact publication name: %s\n' "$name" >&2
        return 1
        ;;
    esac
    if [ ! -s "$STAGING_DIR/$name" ] || [ -L "$STAGING_DIR/$name" ]; then
      printf 'Allowlisted billing artifact is missing, empty, or not a regular file: %s\n' "$STAGING_DIR/$name" >&2
      return 1
    fi
    chmod 600 "$STAGING_DIR/$name"
    artifact_paths+=("$STAGING_DIR/$name")
    artifact_names+=("$name")
  done

  for index in "${!artifact_paths[@]}"; do
    target="$REPORTS_DIR/${artifact_names[$index]}"
    if [ -L "$target" ] || { [ -e "$target" ] && [ ! -f "$target" ]; }; then
      printf 'Published artifact target is not a regular file: %s\n' "$target" >&2
      return 1
    fi
  done

  backup_dir="$(mktemp -d "$REPORTS_DIR/.billing-audit-backup-${SOURCE_RUN_ID}-${RECONCILIATION_ID}.XXXXXX")"
  for index in "${!artifact_paths[@]}"; do
    target="$REPORTS_DIR/${artifact_names[$index]}"
    if [ -f "$target" ]; then
      if ! cp -p "$target" "$backup_dir/${artifact_names[$index]}"; then
        printf 'Could not back up published artifact before promotion: %s\n' "$target" >&2
        return 1
      fi
      prior_exists+=("1")
    else
      prior_exists+=("0")
    fi
  done

  trap 'handle_publication_signal INT' INT
  trap 'handle_publication_signal TERM' TERM
  for index in "${!artifact_paths[@]}"; do
    rollback_limit="$index"
    target="$REPORTS_DIR/${artifact_names[$index]}"
    if ! "$MV_BIN" -f -- "${artifact_paths[$index]}" "$target"; then
      printf 'Artifact promotion failed; restoring the prior published set.\n' >&2
      trap '' INT TERM
      rollback_staged_publication "$rollback_limit"
      trap - INT TERM
      return 1
    fi
  done
  trap - INT TERM

  for backup_artifact in "$backup_dir"/*; do
    if [ -f "$backup_artifact" ]; then
      if ! rm -f -- "$backup_artifact"; then
        printf 'Published successfully, but could not remove backup artifact: %s\n' "$backup_artifact" >&2
      fi
    fi
  done
  if ! rmdir "$backup_dir"; then
    printf 'Published successfully, but could not remove backup directory: %s\n' "$backup_dir" >&2
  fi

  if ! rmdir "$STAGING_DIR"; then
    printf 'Published successfully, but could not remove staging directory: %s\n' "$STAGING_DIR" >&2
  fi
  STAGING_DIR=""
}

stage_publication_file() {
  local source_path="$1"
  local published_name="$2"

  copy_required_file "$source_path" "$STAGING_DIR/$published_name"
  PUBLICATION_ARTIFACT_NAMES+=("$published_name")
}

run_source_collection() {
  local run_parent="$REPORTS_DIR/runs/$MONTH"
  local working_source_dir="$SOURCE_DIR"
  local working_run_dir=""
  local -a manifest_args=()

  if ! is_dry_run; then
    if [ -L "$REPORTS_DIR/runs" ] || { [ -e "$REPORTS_DIR/runs" ] && [ ! -d "$REPORTS_DIR/runs" ]; }; then
      printf 'Billing runs path is not a real directory: %s\n' "$REPORTS_DIR/runs" >&2
      return 1
    fi
    if [ -L "$run_parent" ] || { [ -e "$run_parent" ] && [ ! -d "$run_parent" ]; }; then
      printf 'Billing month run path is not a real directory: %s\n' "$run_parent" >&2
      return 1
    fi
    mkdir -p "$run_parent"
    chmod 700 "$REPORTS_DIR/runs" "$run_parent"
    if [ -e "$SOURCE_RUN_DIR" ] || [ -L "$SOURCE_RUN_DIR" ]; then
      printf 'Immutable source run already exists; use a new SOURCE_RUN_ID: %s\n' "$SOURCE_RUN_DIR" >&2
      return 1
    fi
    working_run_dir="$(mktemp -d "$run_parent/.${SOURCE_RUN_ID}.collect.XXXXXX")"
    STAGING_DIR="$working_run_dir"
    mkdir -m 700 "$working_run_dir/sources"
    working_source_dir="$working_run_dir/sources"
    printf 'Source staging directory: %s\n' "$working_source_dir"
  fi

  run_in_dir "HaloPSA recurring invoice audit" "$ROOT_DIR/connectors/halopsa" \
    "$GO_BIN" run ./cmd/billing-report \
      -config "$HALOPSA_CONFIG" \
      -month "$MONTH" \
      -run-id "$SOURCE_RUN_ID" \
      -out-dir "$working_source_dir" \
      ${SOURCE_OUTPUT_ARGS[@]+"${SOURCE_OUTPUT_ARGS[@]}"}

  if source_enabled "vcenter"; then
    run_in_dir "vCenter billing allocation audit" "$ROOT_DIR/connectors/vcenter" \
      "$GO_BIN" run ./cmd/billing-report \
        -config "$VCENTER_CONFIG" \
        -month "$MONTH" \
        -run-id "$SOURCE_RUN_ID" \
        -out-dir "$working_source_dir" \
        ${SOURCE_OUTPUT_ARGS[@]+"${SOURCE_OUTPUT_ARGS[@]}"}
  fi

  if source_enabled "pax8"; then
    run_in_dir "Pax8 subscription audit" "$ROOT_DIR/connectors/pax8" \
      "$GO_BIN" run ./cmd/billing-report \
        -config "$PAX8_CONFIG" \
        -month "$MONTH" \
        -out-dir "$working_source_dir" \
        -client-mapping "" \
        ${SOURCE_OUTPUT_ARGS[@]+"${SOURCE_OUTPUT_ARGS[@]}"}
  fi

  if source_enabled "sophos"; then
    run_in_dir "Sophos Central billing usage audit" "$ROOT_DIR/connectors/sophos-central" \
      "$GO_BIN" run ./cmd/billing-report \
        -config "$SOPHOS_CONFIG" \
        -month "$MONTH" \
        -out-dir "$working_source_dir" \
        -client-mapping "" \
        ${SOURCE_OUTPUT_ARGS[@]+"${SOURCE_OUTPUT_ARGS[@]}"}
  fi

  if source_enabled "checkpoint"; then
    run_in_dir "Check Point Harmony usage audit" "$ROOT_DIR/connectors/checkpoint-harmony" \
      "$GO_BIN" run ./cmd/billing-report \
        -config "$CHECKPOINT_CONFIG" \
        -month "$MONTH" \
        -out-dir "$working_source_dir" \
        ${CHECKPOINT_EXPORT_ARGS[@]+"${CHECKPOINT_EXPORT_ARGS[@]}"} \
        ${SOURCE_OUTPUT_ARGS[@]+"${SOURCE_OUTPUT_ARGS[@]}"}
  fi

  if source_enabled "veeam"; then
    run_in_dir "Veeam Cloud Connect usage audit" "$ROOT_DIR/connectors/veeam-cloud-connect" \
      "$GO_BIN" run ./cmd/billing-report \
        -config "$VEEAM_CONFIG" \
        -month "$MONTH" \
        -out-dir "$working_source_dir" \
        ${SOURCE_OUTPUT_ARGS[@]+"${SOURCE_OUTPUT_ARGS[@]}"}
  fi

  manifest_args=(
    -halopsa-json "$working_source_dir/halopsa-recurring-invoices-$MONTH.json"
    -client-snapshot "$working_source_dir/halopsa-client-snapshot.json"
  )
  if source_enabled "vcenter"; then
    manifest_args+=(-vcenter-json "$working_source_dir/vcenter-billing-audit-$MONTH.json")
  fi
  if source_enabled "pax8"; then
    manifest_args+=(-pax8-json "$working_source_dir/pax8-subscriptions-$MONTH.json")
  fi
  if source_enabled "sophos"; then
    manifest_args+=(-sophos-json "$working_source_dir/sophos-billing-usage-$MONTH.json")
  fi
  if source_enabled "checkpoint"; then
    manifest_args+=(-checkpoint-json "$working_source_dir/checkpoint-harmony-usage-$MONTH.json")
  fi
  if source_enabled "veeam"; then
    manifest_args+=(-veeam-json "$working_source_dir/veeam-cloud-connect-usage-$MONTH.json")
  fi

  run_in_dir "Seal immutable billing source run" "$ROOT_DIR/workflows/billing-reconciliation" \
    "$GO_BIN" run ./cmd/reconcile \
      -source consolidated \
      -phase seal-sources \
      -month "$MONTH" \
      -source-run-id "$SOURCE_RUN_ID" \
      -selected-sources "$ENABLED_SOURCES" \
      -reports-dir "$working_source_dir" \
      -source-manifest "$working_source_dir/source-manifest.json" \
      "${manifest_args[@]}"

  if ! is_dry_run; then
    validate_source_artifacts "$working_source_dir"
    secure_artifact_tree "$working_source_dir"
    commit_staged_directory "$working_run_dir" "$SOURCE_RUN_DIR"
    SOURCE_DIR="$SOURCE_RUN_DIR/sources"
    printf 'Sealed source run: %s\n' "$SOURCE_RUN_DIR"
  fi
}

run_mapping_review() {
  local attempt_parent="$SOURCE_RUN_DIR/reconciliations"
  local working_attempt_dir="$ATTEMPT_DIR"

  if ! is_dry_run; then
    require_run_directory "$SOURCE_RUN_DIR"
    validate_source_artifacts "$SOURCE_DIR"
    if [ -L "$attempt_parent" ] || { [ -e "$attempt_parent" ] && [ ! -d "$attempt_parent" ]; }; then
      printf 'Reconciliation attempts path is not a real directory: %s\n' "$attempt_parent" >&2
      return 1
    fi
    mkdir -p "$attempt_parent"
    chmod 700 "$attempt_parent"
    if [ -e "$ATTEMPT_DIR" ] || [ -L "$ATTEMPT_DIR" ]; then
      printf 'Reconciliation attempt already exists; use a new RECONCILIATION_ID: %s\n' "$ATTEMPT_DIR" >&2
      return 1
    fi
    working_attempt_dir="$(mktemp -d "$attempt_parent/.${RECONCILIATION_ID}.review.XXXXXX")"
    STAGING_DIR="$working_attempt_dir"
    mkdir -m 700 "$working_attempt_dir/inputs"
  fi

  copy_required_file "$FINAL_CLIENT_CROSSWALK" "$working_attempt_dir/inputs/billing-client-crosswalk.json"
  copy_required_file "$FINAL_SERVICE_LINE_MAPPING" "$working_attempt_dir/inputs/billing-service-line-mapping.json"

  run_in_dir "Offline client mapping review" "$ROOT_DIR/workflows/billing-reconciliation" \
    "$GO_BIN" run ./cmd/reconcile \
      -source consolidated \
      -phase mapping-review \
      -month "$MONTH" \
      -source-run-id "$SOURCE_RUN_ID" \
      -reconciliation-id "$RECONCILIATION_ID" \
      -selected-sources "$ENABLED_SOURCES" \
      -reports-dir "$SOURCE_DIR" \
      -source-manifest "$SOURCE_DIR/source-manifest.json" \
      -client-snapshot "$SOURCE_DIR/halopsa-client-snapshot.json" \
      -client-crosswalk "$working_attempt_dir/inputs/billing-client-crosswalk.json" \
      -service-line-mapping "$working_attempt_dir/inputs/billing-service-line-mapping.json" \
      -out-dir "$working_attempt_dir"

  if ! is_dry_run; then
    validate_mapping_review_artifacts "$working_attempt_dir"
    secure_artifact_tree "$working_attempt_dir"
    commit_staged_directory "$working_attempt_dir" "$ATTEMPT_DIR"
    printf 'Mapping review attempt: %s\n' "$ATTEMPT_DIR"
  fi
}

prepare_publication_stage() {
  local source_path

  if is_dry_run; then
    printf 'DRY RUN: canonical publication would use only the explicit finalized artifact allowlist.\n'
    return
  fi

  STAGING_DIR="$(mktemp -d "$REPORTS_DIR/.billing-audit-publication-${SOURCE_RUN_ID}-${RECONCILIATION_ID}.XXXXXX")"
  PUBLICATION_ARTIFACT_NAMES=()

  stage_publication_file "$SOURCE_DIR/halopsa-recurring-invoices-$MONTH.json" "halopsa-recurring-invoices-$MONTH.json"
  stage_publication_file "$SOURCE_DIR/halopsa-client-snapshot.json" "halopsa-client-snapshot.json"
  if source_workbooks_enabled; then
    stage_publication_file "$SOURCE_DIR/halopsa-recurring-invoices-$MONTH.xlsx" "halopsa-recurring-invoices-$MONTH.xlsx"
  fi
  if source_enabled "vcenter"; then
    stage_publication_file "$SOURCE_DIR/vcenter-billing-audit-$MONTH.json" "vcenter-billing-audit-$MONTH.json"
    if source_workbooks_enabled; then
      stage_publication_file "$SOURCE_DIR/vcenter-billing-audit-$MONTH.xlsx" "vcenter-billing-audit-$MONTH.xlsx"
    fi
  fi
  if source_enabled "pax8"; then
    stage_publication_file "$SOURCE_DIR/pax8-subscriptions-$MONTH.json" "pax8-subscriptions-$MONTH.json"
    if source_workbooks_enabled; then
      stage_publication_file "$SOURCE_DIR/pax8-subscriptions-$MONTH.xlsx" "pax8-subscriptions-$MONTH.xlsx"
    fi
  fi
  if source_enabled "sophos"; then
    stage_publication_file "$SOURCE_DIR/sophos-billing-usage-$MONTH.json" "sophos-billing-usage-$MONTH.json"
    if source_workbooks_enabled; then
      stage_publication_file "$SOURCE_DIR/sophos-billing-usage-$MONTH.xlsx" "sophos-billing-usage-$MONTH.xlsx"
    fi
  fi
  if source_enabled "checkpoint"; then
    stage_publication_file "$SOURCE_DIR/checkpoint-harmony-usage-$MONTH.json" "checkpoint-harmony-usage-$MONTH.json"
    if source_workbooks_enabled; then
      stage_publication_file "$SOURCE_DIR/checkpoint-harmony-usage-$MONTH.xlsx" "checkpoint-harmony-usage-$MONTH.xlsx"
    fi
  fi
  if source_enabled "veeam"; then
    stage_publication_file "$SOURCE_DIR/veeam-cloud-connect-usage-$MONTH.json" "veeam-cloud-connect-usage-$MONTH.json"
    if source_workbooks_enabled; then
      stage_publication_file "$SOURCE_DIR/veeam-cloud-connect-usage-$MONTH.xlsx" "veeam-cloud-connect-usage-$MONTH.xlsx"
    fi
  fi

  stage_publication_file "$ATTEMPT_DIR/billing-client-resolution.json" "billing-client-resolution-$MONTH.json"
  stage_publication_file "$ATTEMPT_DIR/billing-source-facts.json" "billing-source-facts-$MONTH.json"
  stage_publication_file "$ATTEMPT_DIR/billing-reconciliation.json" "billing-reconciliation-$MONTH.json"
  stage_publication_file "$ATTEMPT_DIR/billing-reconciliation.xlsx" "billing-reconciliation-$MONTH.xlsx"
  stage_publication_file "$SOURCE_DIR/source-manifest.json" "billing-source-manifest-$MONTH.json"
  # The run manifest is the canonical pointer and is intentionally promoted last.
  stage_publication_file "$ATTEMPT_DIR/reconciliation-manifest.json" "billing-run-manifest-$MONTH.json"
}

run_finalization() {
  require_run_directory "$SOURCE_RUN_DIR"
  require_run_directory "$ATTEMPT_DIR"
  if ! is_dry_run; then
    validate_source_artifacts "$SOURCE_DIR"
    validate_mapping_review_artifacts "$ATTEMPT_DIR"
  fi

  run_in_dir "Consolidated billing reconciliation (offline)" "$ROOT_DIR/workflows/billing-reconciliation" \
    "$GO_BIN" run ./cmd/reconcile \
      -source consolidated \
      -phase finalize \
      -month "$MONTH" \
      -source-run-id "$SOURCE_RUN_ID" \
      -reconciliation-id "$RECONCILIATION_ID" \
      -selected-sources "$ENABLED_SOURCES" \
      -reports-dir "$SOURCE_DIR" \
      -source-manifest "$SOURCE_DIR/source-manifest.json" \
      -client-snapshot "$SOURCE_DIR/halopsa-client-snapshot.json" \
      -client-crosswalk "$ATTEMPT_DIR/inputs/billing-client-crosswalk.json" \
      -client-resolution "$ATTEMPT_DIR/billing-client-resolution.json" \
      -service-line-mapping "$ATTEMPT_DIR/inputs/billing-service-line-mapping.json" \
      -out-dir "$ATTEMPT_DIR"

  if ! is_dry_run; then
    validate_finalized_artifacts "$ATTEMPT_DIR"
    secure_artifact_tree "$ATTEMPT_DIR"
    prepare_publication_stage
    publish_staged_artifacts "${PUBLICATION_ARTIFACT_NAMES[@]}"
  else
    prepare_publication_stage
  fi
}

finish_audit_success() {
  local message="$1"
  if is_dry_run; then
    return
  fi
  if ! release_audit_lock; then
    trap - EXIT
    printf 'The phase completed, but it cannot be certified complete because its audit lock was not released. Verify run IDs and lock contents before use.\n' >&2
    exit 1
  fi
  trap - EXIT
  printf '\n%s\n' "$message"
}

REPORTS_DIR="$(expand_path "${REPORTS_DIR:-reports}")"
HALOPSA_CONFIG="$(expand_path "${HALOPSA_CONFIG:-~/.codex/halopsa-mcp/config.json}")"
VCENTER_CONFIG="$(expand_path "${VCENTER_CONFIG:-~/.codex/vcenter-mcp/config.json}")"
PAX8_CONFIG="$(expand_path "${PAX8_CONFIG:-~/.codex/pax8-mcp/config.json}")"
SOPHOS_CONFIG="$(expand_path "${SOPHOS_CONFIG:-~/.codex/sophos-central-mcp/config.json}")"
CHECKPOINT_CONFIG="$(expand_path "${CHECKPOINT_CONFIG:-~/.codex/checkpoint-harmony-mcp/config.json}")"
VEEAM_CONFIG="$(expand_path "${VEEAM_CONFIG:-~/.codex/veeam-cloud-connect-mcp/config.json}")"
REQUESTED_SOURCES="$(normalize_sources "$SOURCES")"

validate_month
validate_audit_phase
validate_boolean "DRY_RUN" "$DRY_RUN"
validate_boolean "SOURCE_WORKBOOKS" "$SOURCE_WORKBOOKS"
validate_sources "$REQUESTED_SOURCES"
if [ "$REQUESTED_SOURCES" = "all" ]; then
  ENABLED_SOURCES="vcenter,pax8,sophos,checkpoint,veeam"
else
  ENABLED_SOURCES="$REQUESTED_SOURCES"
fi

if phase_collects_sources; then
  SOURCE_RUN_ID="${SOURCE_RUN_ID:-billing-${MONTH}-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
elif [ -z "$SOURCE_RUN_ID" ]; then
  printf 'SOURCE_RUN_ID is required for AUDIT_PHASE=%s.\n' "$AUDIT_PHASE" >&2
  exit 1
fi
if [ "$AUDIT_PHASE" = "full" ]; then
  RECONCILIATION_ID="${RECONCILIATION_ID:-reconcile-${MONTH}-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
elif phase_builds_mapping_review || phase_finalizes; then
  if [ -z "$RECONCILIATION_ID" ]; then
    printf 'RECONCILIATION_ID is required for AUDIT_PHASE=%s.\n' "$AUDIT_PHASE" >&2
    exit 1
  fi
fi
validate_identifier "SOURCE_RUN_ID" "$SOURCE_RUN_ID"
if [ -n "$RECONCILIATION_ID" ]; then
  validate_identifier "RECONCILIATION_ID" "$RECONCILIATION_ID"
fi

if source_workbooks_enabled; then
  SOURCE_OUTPUT_ARGS=(-json-only=false)
else
  SOURCE_OUTPUT_ARGS=(-json-only)
fi
if [ -n "$CHECKPOINT_ACCOUNTS_EXPORT_RAW" ]; then
  CHECKPOINT_ACCOUNTS_EXPORT_PATH="$(expand_path "$CHECKPOINT_ACCOUNTS_EXPORT_RAW")"
  CHECKPOINT_EXPORT_ARGS=(-accounts-export "$CHECKPOINT_ACCOUNTS_EXPORT_PATH")
fi

validate_reports_dir "$REPORTS_DIR"
REPORTS_DIR="$(canonicalize_reports_dir "$REPORTS_DIR")"
validate_reports_dir "$REPORTS_DIR"

FINAL_CLIENT_CROSSWALK="$(expand_path "${CLIENT_CROSSWALK_RAW:-$REPORTS_DIR/billing-client-crosswalk.json}")"
FINAL_SERVICE_LINE_MAPPING="$(expand_path "${SERVICE_LINE_MAPPING_RAW:-$REPORTS_DIR/billing-service-line-mapping.json}")"
SOURCE_RUN_DIR="$REPORTS_DIR/runs/$MONTH/$SOURCE_RUN_ID"
SOURCE_DIR="$SOURCE_RUN_DIR/sources"
if [ -n "$RECONCILIATION_ID" ]; then
  ATTEMPT_DIR="$SOURCE_RUN_DIR/reconciliations/$RECONCILIATION_ID"
fi

if phase_collects_sources; then
  require_file "$HALOPSA_CONFIG"
  if source_enabled "vcenter"; then
    require_file "$VCENTER_CONFIG"
  fi
  if source_enabled "pax8"; then
    require_file "$PAX8_CONFIG"
  fi
  if source_enabled "sophos"; then
    require_file "$SOPHOS_CONFIG"
  fi
  if source_enabled "checkpoint"; then
    require_file "$CHECKPOINT_CONFIG"
    if [ -n "$CHECKPOINT_ACCOUNTS_EXPORT_PATH" ]; then
      require_file "$CHECKPOINT_ACCOUNTS_EXPORT_PATH"
    fi
  fi
  if source_enabled "veeam"; then
    require_file "$VEEAM_CONFIG"
  fi
fi
if phase_builds_mapping_review; then
  require_file "$FINAL_CLIENT_CROSSWALK"
  require_file "$FINAL_SERVICE_LINE_MAPPING"
fi
if [ "$AUDIT_PHASE" = "mapping-review" ] || [ "$AUDIT_PHASE" = "finalize" ]; then
  require_run_directory "$SOURCE_RUN_DIR"
  require_file "$SOURCE_DIR/source-manifest.json"
fi
if [ "$AUDIT_PHASE" = "finalize" ]; then
  require_run_directory "$ATTEMPT_DIR"
  require_file "$ATTEMPT_DIR/inputs/billing-client-crosswalk.json"
  require_file "$ATTEMPT_DIR/inputs/billing-service-line-mapping.json"
  require_file "$ATTEMPT_DIR/billing-client-resolution.json"
fi

printf 'Monthly billing audit\n'
printf 'Phase: %s\n' "$AUDIT_PHASE"
printf 'Source run ID: %s\n' "$SOURCE_RUN_ID"
if [ -n "$RECONCILIATION_ID" ]; then
  printf 'Reconciliation ID: %s\n' "$RECONCILIATION_ID"
fi
printf 'Run date: %s\n' "$RUN_DATE"
printf 'Billing month: %s\n' "$MONTH"
printf 'Target invoice date: first day of the month after %s\n' "$MONTH"
printf 'Sources: %s\n' "$ENABLED_SOURCES"
printf 'Reports directory: %s\n' "$REPORTS_DIR"
printf 'Source run directory: %s\n' "$SOURCE_RUN_DIR"
if [ -n "$ATTEMPT_DIR" ]; then
  printf 'Reconciliation attempt directory: %s\n' "$ATTEMPT_DIR"
fi
if source_enabled "checkpoint" && [ -n "$CHECKPOINT_ACCOUNTS_EXPORT_PATH" ]; then
  printf 'Check Point accounts export: %s\n' "$CHECKPOINT_ACCOUNTS_EXPORT_PATH"
fi
if source_workbooks_enabled; then
  printf 'Source connector workbooks: enabled for diagnostics\n'
else
  printf 'Source connector workbooks: disabled, JSON source artifacts only\n'
fi
if is_dry_run; then
  printf 'Mode: dry run; commands are printed and no APIs or files are touched\n'
else
  mkdir -p "$REPORTS_DIR"
  REPORTS_DIR="$(canonicalize_reports_dir "$REPORTS_DIR")"
  validate_reports_dir "$REPORTS_DIR"
  acquire_audit_lock
fi

case "$AUDIT_PHASE" in
  collect)
    run_source_collection
    finish_audit_success "Source collection complete for $MONTH. Sealed source run $SOURCE_RUN_ID."
    ;;
  mapping-review)
    run_mapping_review
    finish_audit_success "Mapping review complete for source run $SOURCE_RUN_ID, attempt $RECONCILIATION_ID. No vendor APIs were called."
    ;;
  finalize)
    run_finalization
    finish_audit_success "Billing reconciliation published for source run $SOURCE_RUN_ID, attempt $RECONCILIATION_ID. No vendor APIs were called."
    ;;
  full)
    run_source_collection
    run_mapping_review
    run_finalization
    finish_audit_success "Monthly billing audit complete for $MONTH. Published source run $SOURCE_RUN_ID, attempt $RECONCILIATION_ID."
    ;;
esac
