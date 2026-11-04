"""Independent, content-free service health and change notifications."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time


def report(store, config, now=None):
    now = time.time() if now is None else now
    maximum_age = config.get("health_max_age_seconds", 300)
    heartbeat = store.setting("service_heartbeat")
    issues = []
    if store.setting("service_active") != "1":
        issues.append({"code": "service_not_running"})
    elif heartbeat is None or now - float(heartbeat) > maximum_age:
        issues.append({"code": "service_heartbeat_stale"})
    if store.setting("service_mode") == "intake":
        discovery = store.setting("last_discovery_success")
        if store.setting("discovery_error", ""):
            issues.append({"code": "discovery_error"})
        elif discovery is None or now - float(discovery) > max(maximum_age, 2 * config.get("poll_seconds", 15)):
            issues.append({"code": "discovery_stale"})
    for row in store.status()["tickets"]:
        if row["state"] == "uncertain":
            issues.append({"code": "write_needs_readback", "ticket_id": row["id"]})
        elif row["error"]:
            issues.append({"code": "ticket_processing_error", "ticket_id": row["id"]})
    # A decision can use its full timeout, followed by several bounded connector
    # reads/writes. This detects a stuck job without cancelling accepted writes.
    job_age = config.get("health_job_age_seconds", 1800)
    for ticket_id, started in json.loads(store.setting("active_jobs", "{}")).items():
        if now - started > job_age:
            issues.append({"code": "ticket_job_stale", "ticket_id": int(ticket_id)})
    return {"healthy": not issues, "mode": store.setting("service_mode", "unknown"),
            "issues": issues}


def notify_changes(store, config, health):
    command = config.get("health_notify_command")
    if not command:
        return False
    # Ages, failure counts, and client data are deliberately absent, so polling
    # the same incident does not generate repeated messages.
    current = json.dumps(health, sort_keys=True)
    previous = store.setting("health_last_notified")
    if current == previous or (previous is None and health["healthy"]):
        return False
    subprocess.run(command, input=current, text=True, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
    store.set_setting("health_last_notified", current)
    return True


class NotificationState:
    """Keep alert receipts independent of the worker config and ticket database."""
    def __init__(self, directory):
        self.path = directory / "health-notification.json"
        self.error = False
        self.values = {}
        try:
            self.values = json.loads(self.path.read_text())
            if not isinstance(self.values, dict) or not all(
                    isinstance(value, str) for value in self.values.values()):
                raise ValueError("Invalid notification receipt")
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            # A corrupt receipt is itself an incident; it must not disable the
            # channel that reports it. Successful notification replaces it.
            self.error = True
            self.values = {}

    def setting(self, key):
        return self.values.get(key)

    def set_setting(self, key, value):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({key: value}))
        temporary.replace(self.path)
        self.values = {key: value}


def main():
    # The timer supplies paths and notifier argv directly. It can therefore
    # report a broken worker configuration or SQLite database independently.
    from .__main__ import load_config
    from .store import Store
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--notify-command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    args.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (args.state_dir / "health.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        store = None
        try:
            config = load_config(args.config)
            store = Store(Path(config["state_dir"]) / "relay.sqlite3")
            health = report(store, config)
        except Exception:
            health = {"healthy": False, "mode": "unknown",
                      "issues": [{"code": "health_check_failed"}]}
        finally:
            if store:
                store.db.close()
        notification_state = NotificationState(args.state_dir)
        if notification_state.error:
            health["healthy"] = False
            health["issues"].append({"code": "notification_state_unreadable"})
        try:
            health["notification_sent"] = notify_changes(notification_state,
                {"health_notify_command": args.notify_command}, health)
        except Exception as exc:
            health["notification_error"] = type(exc).__name__
        print(json.dumps(health, indent=2))
        return 2 if "notification_error" in health else int(not health["healthy"])


if __name__ == "__main__":
    raise SystemExit(main())
