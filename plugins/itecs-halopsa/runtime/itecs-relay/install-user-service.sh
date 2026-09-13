#!/usr/bin/env bash
set -euo pipefail
runtime_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
relay_config="${1:-$HOME/.config/itecs-relay/config.json}"
ticket_args=""
if [[ -n "${2:-}" ]]; then
  [[ "$2" =~ ^[1-9][0-9]*$ ]] || { printf 'Second argument must be a positive ticket ID\n' >&2; exit 2; }
  ticket_args=" --ticket $2"
fi
python_path="$(command -v python3)"
health_command="$("$python_path" - "$relay_config" "$python_path" <<'PY'
import json, sys
from pathlib import Path
config = json.loads(Path(sys.argv[1]).read_text())
argv = [sys.argv[2], '-m', 'relay.health', '--config', sys.argv[1],
        '--state-dir', config['state_dir']]
if config.get('health_notify_command'):
    argv += ['--notify-command', *config['health_notify_command']]
print(' '.join(json.dumps(arg, ensure_ascii=False).replace('%', '%%') for arg in argv))
PY
)"
[[ "$runtime_root" != *'"'* && "$relay_config" != *'"'* ]]
mkdir -p "$HOME/.config/systemd/user"
unit_path="$HOME/.config/systemd/user/itecs-relay.service"
cat > "$unit_path" <<EOF
[Unit]
Description=ITECS RELAY HaloPSA support conversations
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$runtime_root
ExecStart="$python_path" -m relay --config "$relay_config" serve$ticket_args
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
UMask=0077
Restart=on-failure
RestartSec=15
KillMode=control-group
TimeoutStopSec=20

[Install]
WantedBy=default.target
EOF
cat > "$HOME/.config/systemd/user/itecs-relay-health.service" <<EOF
[Unit]
Description=ITECS RELAY independent health check

[Service]
Type=oneshot
WorkingDirectory=$runtime_root
ExecStart=$health_command
UMask=0077
TimeoutStartSec=90
EOF
cat > "$HOME/.config/systemd/user/itecs-relay-health.timer" <<EOF
[Unit]
Description=Check ITECS RELAY health every minute

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
Unit=itecs-relay-health.service

[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload
printf 'Installed %s\n' "$unit_path"
printf 'Run readiness: cd %q && %q -m relay --config %q check\n' "$runtime_root" "$python_path" "$relay_config"
printf 'Start: systemctl --user enable --now itecs-relay.service itecs-relay-health.timer\n'
