#!/usr/bin/env bash
set -euo pipefail
runtime_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
relay_config="${1:-$HOME/.config/itecs-relay/config.json}"
python_path="$(command -v python3)"
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
ExecStart="$python_path" -m relay --config "$relay_config" serve
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
UMask=0077
Restart=on-failure
RestartSec=15
KillMode=control-group
TimeoutStopSec=20

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
printf 'Installed %s\n' "$unit_path"
printf 'Run readiness: cd %q && %q -m relay --config %q check\n' "$runtime_root" "$python_path" "$relay_config"
printf 'Start: systemctl --user enable --now itecs-relay.service\n'
