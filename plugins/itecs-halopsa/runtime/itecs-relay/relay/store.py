"""SQLite owns delivery receipts and conversation progress across restarts."""

import json
import os
import sqlite3
import time
from pathlib import Path


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(path, timeout=30)
        os.chmod(path, 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=FULL;
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tickets (
              id INTEGER PRIMARY KEY, state TEXT NOT NULL DEFAULT 'new',
              snapshot TEXT NOT NULL DEFAULT '', context TEXT NOT NULL DEFAULT '{}',
              plan TEXT, due REAL NOT NULL DEFAULT 0, failures INTEGER NOT NULL DEFAULT 0,
              error TEXT, updated REAL NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS operations (
              id TEXT PRIMARY KEY, ticket_id INTEGER NOT NULL, kind TEXT NOT NULL,
              arguments TEXT NOT NULL, before_ids TEXT NOT NULL, state TEXT NOT NULL,
              receipt TEXT, created REAL NOT NULL);
        """)

    def setting(self, key, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, value))

    def enroll(self, ticket_id):
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO tickets(id) VALUES (?)", (ticket_id,))

    def ticket(self, ticket_id):
        row = self.db.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        return dict(row) if row else None

    def save(self, ticket_id, **values):
        values["updated"] = time.time()
        columns = ",".join(key + "=?" for key in values)
        with self.db:
            self.db.execute("UPDATE tickets SET " + columns + " WHERE id=?",
                            (*values.values(), ticket_id))

    def due(self):
        return [row[0] for row in self.db.execute("""SELECT id FROM tickets
            WHERE state != 'uncertain' AND
              (plan IS NOT NULL OR state NOT IN ('handed_off','resolved','ignored')) AND due<=?
            ORDER BY due,id""", (time.time(),))]

    def begin_operation(self, op_id, ticket_id, kind, arguments, before_ids):
        with self.db:
            self.db.execute("""INSERT INTO operations VALUES (?,?,?,?,?,'dispatching',NULL,?)
                ON CONFLICT(id) DO UPDATE SET arguments=excluded.arguments,
                  before_ids=excluded.before_ids, state='dispatching', receipt=NULL,
                  created=excluded.created WHERE operations.state='not_attempted'""",
                            (op_id, ticket_id, kind, json.dumps(arguments),
                             json.dumps(before_ids), time.time()))

    def reject_operation(self, op_id, ticket_id):
        with self.db:
            self.db.execute("UPDATE operations SET state='not_attempted' WHERE id=?", (op_id,))
            # Rejection and removal of the stale plan survive the same crash.
            self.db.execute("UPDATE tickets SET plan=NULL WHERE id=?", (ticket_id,))

    def operation(self, op_id):
        row = self.db.execute("SELECT * FROM operations WHERE id=?", (op_id,)).fetchone()
        return dict(row) if row else None

    def receipt(self, op_id, value):
        with self.db:
            self.db.execute("UPDATE operations SET state='verified',receipt=? WHERE id=?",
                            (json.dumps(value), op_id))

    def status(self):
        return {"tickets": [dict(row) for row in self.db.execute(
            "SELECT id,state,due,failures,error,updated FROM tickets ORDER BY id")],
                "discovery_cursor": self.setting("cursor"),
                "operations": [dict(row) for row in self.db.execute(
                    "SELECT id,ticket_id,kind,state FROM operations ORDER BY created")]}
