"""Consume the existing HaloPSA connector over its native stdio protocol."""

import json
import queue
import subprocess
import threading


class ConnectorError(RuntimeError):
    pass


class TicketChangedBeforeWrite(ConnectorError):
    """The connector proved this request never reached a write."""


class MCP:
    def __init__(self, command, timeout=120):
        self.timeout = timeout
        self.serial = 0
        self.messages = queue.Queue()
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True, bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()
        self.request("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                    "clientInfo": {"name": "itecs-relay", "version": "0.1.0"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _read(self):
        try:
            for line in self.process.stdout:
                self.messages.put(json.loads(line))
        except (ValueError, OSError):
            pass
        finally:
            self.messages.put(None)

    def _send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method, params):
        self.serial += 1
        serial = self.serial
        try:
            self._send({"jsonrpc": "2.0", "id": serial, "method": method, "params": params})
            while True:
                message = self.messages.get(timeout=self.timeout)
                if message is None:
                    raise ConnectorError("connector exited")
                if message.get("id") != serial:
                    continue
                if "error" in message:
                    raise ConnectorError("connector protocol error")
                return message["result"]
        except (queue.Empty, BrokenPipeError, OSError) as exc:
            self.close()
            raise ConnectorError("connector transport interrupted") from exc

    def call(self, name, **arguments):
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            structured = result.get("structuredContent")
            detail = structured.get("error") if isinstance(structured, dict) else None
            if (isinstance(detail, dict) and detail.get("code") == "ticket_changed"
                    and detail.get("write_attempted") is False):
                raise TicketChangedBeforeWrite("ticket changed before write")
            # Vendor errors can contain client details or credential-provider stderr.
            raise ConnectorError("Halo tool failed: " + name)
        if not isinstance(result.get("structuredContent"), dict):
            raise ConnectorError("missing structured tool result: " + name)
        return result["structuredContent"]

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()


class Halo:
    def __init__(self, mcp, server_id):
        self.mcp, self.server_id = mcp, server_id

    def call(self, name, **arguments):
        return self.mcp.call("halopsa." + name, server_id=self.server_id, **arguments)

    def collection(self, name, **arguments):
        page, rows, seen = 1, [], set()
        while True:
            result = self.call(name, page_no=page, page_size=100, **arguments)["result"]
            items = result["items"]
            ids = [item["id"] for item in items]
            if len(set(ids)) != len(ids) or seen.intersection(ids):
                raise ConnectorError("pagination repeated an item: " + name)
            seen.update(ids)
            rows.extend(items)
            total = result.get("page", {}).get("record_count")
            if total is not None:
                if len(rows) > total or (not items and len(rows) != total):
                    raise ConnectorError("incomplete collection: " + name)
                if len(rows) == total:
                    return rows
            elif not items:
                return rows
            page += 1

    def ticket(self, ticket_id):
        return self.call("tickets.get", ticket_id=str(ticket_id),
                         include_actions=False)["ticket"]["item"]

    def actions(self, ticket_id):
        return self.collection("ticket_actions.list", ticket_id=str(ticket_id),
                               include_html_note=True, include_html_email=True)

    def statuses(self, ticket_id):
        return self.call("ticket_statuses.list", ticket_id=ticket_id)["result"]["items"]
