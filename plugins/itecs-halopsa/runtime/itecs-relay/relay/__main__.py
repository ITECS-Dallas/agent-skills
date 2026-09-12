"""python3 -m relay --config PATH check|inspect|process|serve|status|resume"""

import argparse
import concurrent.futures
import fcntl
import json
import logging
import os
import signal
import threading
import time
from pathlib import Path

from .decision import Codex
from .mcp import Halo, MCP
from .store import Store
from .worker import Changed, Uncertain, Worker


def load_config(path):
    cfg = json.loads(Path(path).read_text())
    for key in ("workspace", "documentation_root", "skill_path", "state_dir", "codex_command"):
        if not isinstance(cfg.get(key), str) or not Path(cfg[key]).is_absolute():
            raise ValueError("absolute path required: " + key)
    if not Path(cfg["documentation_root"]).is_dir() or not Path(cfg["skill_path"]).is_file():
        raise ValueError("documentation or workflow skill unavailable")
    if not Path(cfg["documentation_root"]).resolve().is_relative_to(Path(cfg["workspace"]).resolve()):
        raise ValueError("documentation_root must be inside workspace")
    for key in ("agent_id", "email_outcome_id", "closed_status_id", "poll_seconds", "workers"):
        if type(cfg.get(key)) is not int or cfg[key] <= 0:
            raise ValueError("positive integer required: " + key)
    if not cfg.get("server_id") or not isinstance(cfg.get("connector_command"), list):
        raise ValueError("server_id and connector_command are required")
    if not cfg["connector_command"] or not all(isinstance(v, str) for v in cfg["connector_command"]):
        raise ValueError("connector_command must be a nonempty argv list")
    return cfg


def connect(cfg):
    mcp = MCP(cfg["connector_command"])
    halo = Halo(mcp, cfg["server_id"])
    if halo.call("agents.me")["agent"]["id"] != cfg["agent_id"]:
        mcp.close()
        raise ValueError("connector identity does not match configured Relay agent")
    return mcp, halo


def log(event, **values):
    logging.info(json.dumps({"event": event, **values}))


def run_ticket(cfg, ticket_id):
    store = Store(Path(cfg["state_dir"]) / "relay.sqlite3")
    mcp = None
    try:
        mcp, halo = connect(cfg)
        decision = Worker(cfg, store, halo, Codex(cfg)).one(ticket_id)
        log("ticket_processed", ticket_id=ticket_id, decision=decision)
    except Changed:
        store.save(ticket_id, plan=None, due=time.time(), error=None)
        log("ticket_changed", ticket_id=ticket_id)
    except Uncertain:
        store.save(ticket_id, state="uncertain", error="Write requires Halo readback; run resume after review")
        log("write_uncertain", ticket_id=ticket_id)
    except Exception as exc:
        row = store.ticket(ticket_id)
        failures = row["failures"] + 1
        store.save(ticket_id, failures=failures,
                   error=type(exc).__name__, due=time.time() + min(900, 15 * 2 ** min(failures, 6)))
        log("ticket_error", ticket_id=ticket_id, error=type(exc).__name__, failures=failures)
    finally:
        if mcp:
            mcp.close()
        store.db.close()


def serve(cfg, store, ticket_id=None):
    lock = open(Path(cfg["state_dir"]) / "worker.lock", "a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    inflight = {}
    next_discovery = 0
    if ticket_id is not None:
        mcp, halo = connect(cfg)
        try:
            Worker(cfg, store, halo, Codex(cfg)).enroll_ticket(ticket_id)
        finally:
            mcp.close()
        log("named_ticket_service", ticket_id=ticket_id)
    with concurrent.futures.ThreadPoolExecutor(max_workers=cfg["workers"]) as executor:
        while not stop.is_set():
            if ticket_id is None and time.monotonic() >= next_discovery:
                mcp = None
                try:
                    mcp, halo = connect(cfg)
                    count = Worker(cfg, store, halo, Codex(cfg)).discover()
                    store.set_setting("last_discovery_success", str(time.time()))
                    store.set_setting("discovery_error", "")
                    log("discovery", rows=count)
                except Exception as exc:
                    store.set_setting("discovery_error", type(exc).__name__)
                    log("discovery_error", error=type(exc).__name__)
                finally:
                    if mcp:
                        mcp.close()
                next_discovery = time.monotonic() + cfg["poll_seconds"]
            inflight = {key: future for key, future in inflight.items() if not future.done()}
            for due_id in store.due():
                if ticket_id is not None and due_id != ticket_id:
                    continue
                if len(inflight) >= cfg["workers"]:
                    break
                if due_id not in inflight:
                    inflight[due_id] = executor.submit(run_ticket, cfg, due_id)
            # Refill free workers promptly; discovery and per-ticket due times keep
            # their own poll interval instead of throttling the whole queue to two.
            stop.wait(1)
    lock.close()


def main():
    os.umask(0o077)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("command", choices=("check", "inspect", "process", "serve", "status", "resume"))
    parser.add_argument("--ticket", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg = load_config(args.config)
    store = Store(Path(cfg["state_dir"]) / "relay.sqlite3")
    if args.command == "status":
        status = store.status()
        status["discovery_error"] = store.setting("discovery_error", "")
        status["last_discovery_success"] = store.setting("last_discovery_success")
        print(json.dumps(status, indent=2))
        return int(bool(status["discovery_error"]) or any(
            row["error"] for row in status["tickets"]))
    if args.command == "serve":
        if args.ticket is not None and args.ticket <= 0:
            parser.error("--ticket must be positive")
        serve(cfg, store, args.ticket)
        return 0
    if args.command == "resume":
        if not args.ticket or not store.ticket(args.ticket):
            parser.error("resume requires an existing --ticket")
        # Keep the durable plan/operations so resumption cannot resend an uncertain write.
        store.save(args.ticket, state="troubleshooting", due=0, error=None)
        return 0
    if args.command == "process":
        if not args.ticket or args.ticket <= 0:
            parser.error("process requires a positive --ticket")
        # Share the service lock so a one-shot run cannot race the resident worker.
        with open(Path(cfg["state_dir"]) / "worker.lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            mcp, halo = connect(cfg)
            try:
                Worker(cfg, store, halo, Codex(cfg)).enroll_ticket(args.ticket)
            finally:
                mcp.close()
            run_ticket(cfg, args.ticket)
        row = store.ticket(args.ticket)
        print(json.dumps({"ticket_id": args.ticket, "state": row["state"], "error": row["error"]}))
        return int(bool(row["error"]))
    mcp, halo = connect(cfg)
    try:
        if args.command == "check":
            names = {t["name"] for t in mcp.request("tools/list", {})["tools"]}
            required = {"halopsa." + n for n in ("tickets.list", "tickets.get", "ticket_actions.list",
                        "ticket_actions.send_email", "ticket_actions.create_private_note",
                        "tickets.update_status", "ticket_statuses.list", "ticket_outcomes.get")}
            if not names.issuperset(required):
                raise ValueError("installed connector is missing Relay tools")
            print(json.dumps({"ready": True, "agent_id": cfg["agent_id"], "tools": len(names),
                              "workspace": cfg["workspace"], "documentation_root": cfg["documentation_root"]}))
        else:
            if not args.ticket or not args.output:
                parser.error("inspect requires --ticket and --output")
            bundle = Worker(cfg, store, halo, Codex(cfg)).one(args.ticket, inspect=True)
            args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            args.output.write_text(json.dumps(bundle, indent=2))
            args.output.chmod(0o600)
            print(json.dumps({"ticket_id": args.ticket, "inspection": str(args.output),
                              "writes": 0, "decision": bundle["plan"]["decision"] if bundle else "unchanged"}))
    finally:
        mcp.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
