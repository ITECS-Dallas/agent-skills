"""Persist each decision and verify each write before advancing a conversation."""

import hashlib
import html
import json
import re
import time
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
from html.parser import HTMLParser
from pathlib import Path

from .decision import schema
from .documentation import documentation_roots
from .mcp import TicketChangedBeforeWrite


class Changed(RuntimeError):
    """Fresh Halo evidence superseded a prepared decision."""


class Uncertain(RuntimeError):
    """A write was attempted but its result cannot yet be independently proved."""


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(
        tzinfo=timezone.utc) if not re.search(r"[+-]\d\d:\d\d$", value) else datetime.fromisoformat(value)


class MailText(HTMLParser):
    def __init__(self, quoted=False):
        super().__init__()
        self.parts, self.skip, self.quoted, self.stopped = [], 0, quoted, False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.quoted and attrs.get("id", "").lower() == "divrplyfwdmsg":
            self.stopped = True
        if self.skip:
            self.skip += tag not in ("br", "hr", "img", "input", "meta", "link")
        elif tag in ("script", "style") or (self.quoted and
                (tag == "blockquote" or "gmail_quote" in attrs.get("class", "") or
                 attrs.get("id", "").lower() == "divrplyfwdmsg")):
            self.skip = 1
        elif tag in ("p", "div", "br", "li", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("br", "hr", "img", "input", "meta", "link"):
            return
        if self.skip:
            self.skip -= 1
        elif tag in ("p", "div", "li", "tr"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip and not self.stopped:
            self.parts.append(data)


def text(value, fresh=False):
    parser = MailText(quoted=fresh)
    parser.feed(str(value or ""))
    result = html.unescape("".join(parser.parts))
    if fresh:
        result = re.split(r"(?im)^\s*(?:On .+wrote:|From:\s|[-_]{3,}.*(?:original|forwarded)|>).*", result)[0]
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", result)).strip()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def email_html(reply):
    """Render plain reply paragraphs and numbered steps as email-safe HTML."""
    blocks, paragraph, steps = [], [], []

    def flush():
        if paragraph:
            blocks.append('<p style="margin:0 0 16px;">' +
                          "<br>".join(html.escape(line) for line in paragraph) + "</p>")
            paragraph.clear()
        if steps:
            blocks.append('<ol style="margin:0 0 16px;padding-left:24px;">' +
                          "".join('<li style="margin:0 0 8px;">' + html.escape(step) +
                                  "</li>" for step in steps) + "</ol>")
            steps.clear()

    for line in reply.strip().splitlines():
        line = line.strip()
        numbered = re.match(r"^\d+[.)]\s+(.+)$", line)
        if numbered:
            if paragraph:
                flush()
            steps.append(numbered[1])
        elif not line:
            # Blank lines between numbered steps do not restart numbering.
            if paragraph:
                flush()
        else:
            if steps:
                flush()
            paragraph.append(line)
    flush()
    return '<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.5;">' + "".join(blocks) + "</div>"


def fingerprint(ticket, actions):
    return hashlib.sha256(canonical([ticket, actions]).encode()).hexdigest()


def action_view(action, ticket, relay_agent_id):
    agent = action.get("actionby_agent_id") or action.get("who_agentid") or 0
    user = action.get("actionby_user_id") or 0
    sender = parseaddr(str(action.get("emailfrom", "")))[1].lower()
    contact = parseaddr(str(ticket.get("user_email", "")))[1].lower()
    private = bool(action.get("hiddenfromuser"))
    if agent == relay_agent_id:
        source = "relay"
    elif action.get("action_systemid", 0) != 0:
        source = "system"
    elif agent > 0:
        source = "agent"
    elif not private and action.get("emaildirection") != "O" and not action.get("sendemail") and (
                         (user > 0 and user == ticket.get("user_id")) or
                          (sender and contact and sender == contact)):
        source = "client"
    else:
        source = "other"
    body = action.get("note") or action.get("emailbody_html") or ""
    fresh_body = action.get("emailbody_html") or action.get("note_html") or body
    return {"id": action["id"], "source": source, "agent_id": agent, "user_id": user,
            "datetime": action.get("datetime") or action.get("actiondatecreated"),
            "private": private, "actiontype": action.get("actiontype", ""),
            "text": text(body), "fresh_text": text(fresh_body, fresh=True),
            "emailto": action.get("emailto", ""), "sendemail": action.get("sendemail", False),
            "email_subject": action.get("emailsubject") or action.get("emailsubjectnew") or ""}


def snapshot(halo, ticket_id, relay_agent_id):
    ticket = halo.ticket(ticket_id)
    actions = sorted((action_view(a, ticket, relay_agent_id) for a in halo.actions(ticket_id)),
                     key=lambda a: (a["datetime"] or "", a["id"]))
    fields = ("id", "summary", "details", "client_id", "client_name", "site_id", "site_name",
              "user_id", "user_name", "user_email", "agent_id", "team_id", "tickettype_id",
              "status_id", "last_update", "dateoccurred", "dateoccured", "source", "closed",
              "workflow_id", "workflow_step", "workflow_seq")
    ticket = {key: ticket[key] for key in fields if key in ticket}
    return ticket, actions


def validate_plan(plan, context, cfg):
    properties = schema()["properties"]
    if not isinstance(plan, dict) or set(plan) != set(properties):
        raise ValueError("decision fields differ from schema")
    for key, spec in properties.items():
        kind = spec["type"]
        if ((kind == "string" and not isinstance(plan[key], str)) or
                (kind == "integer" and type(plan[key]) is not int) or
                (kind == "array" and (not isinstance(plan[key], list) or
                                      not all(isinstance(v, str) for v in plan[key])))):
            raise ValueError("invalid decision field: " + key)
    decision = plan["decision"]
    if decision not in properties["decision"]["enum"]:
        raise ValueError("unknown decision")
    stage = context["state"]
    if decision == "offer" and stage != "new":
        raise ValueError("already offered help")
    if decision in ("instructions", "decline", "resolve") and stage == "new":
        raise ValueError("conversation has not started")
    if decision in ("offer", "instructions", "clarify", "decline") and not plan["reply"].strip():
        raise ValueError("reply is required")
    if decision in ("wait", "ignore") and plan["reply"].strip():
        raise ValueError("this decision does not send an email")
    if decision != "offer" and plan["reply"] and not context["new_client_actions"]:
        raise ValueError("no new client message to answer")
    roots = documentation_roots(cfg, context["ticket"])
    for source in plan["sources"]:
        path = Path(source).resolve()
        if not any(path.is_relative_to(root) for root in roots) or not path.is_file():
            raise ValueError("documentation source is outside this client's readable scopes")
    if decision == "resolve":
        incoming = context["new_client_actions"]
        confirmation = next((a for a in incoming if a["id"] == plan["confirmation_action_id"]), None)
        if confirmation is None:
            raise ValueError("confirmation must identify a new client message")
        quote = plan["confirmation_quote"].strip()
        if not quote or quote not in confirmation["fresh_text"]:
            raise ValueError("confirmation is not in the fresh client message")
        if not plan["private_note"].strip():
            raise ValueError("resolution work note is required")
    return plan


class Worker:
    def __init__(self, cfg, store, halo, model):
        self.cfg, self.store, self.halo, self.model = cfg, store, halo, model

    def enroll_ticket(self, ticket_id):
        """An explicit named-ticket request starts from its current handoff history."""
        if self.store.ticket(ticket_id):
            return
        ticket, actions = snapshot(self.halo, ticket_id, self.cfg["agent_id"])
        self.store.enroll(ticket_id)
        self.store.save(ticket_id, context=json.dumps({
            "manually_enrolled": True, "owner": ticket.get("agent_id"),
            "known_agent_action_ids": [a["id"] for a in actions if a["source"] == "agent"]}))

    def discover(self):
        now = utc_now()
        start = self.store.setting("cursor")
        if start is None:
            # The service takes responsibility for new intake from activation onward.
            self.store.set_setting("activated_at", now)
            self.store.set_setting("cursor", now)
            return 0
        activated = timestamp(self.store.setting("activated_at"))
        overlap = max(timestamp(start) - timedelta(seconds=120), activated).isoformat()
        tickets = self.halo.collection("tickets.list", datesearch="dateoccured",
                                       startdate=overlap, enddate=now, include_closed=True)
        for ticket in tickets:
            created = ticket.get("dateoccurred") or ticket.get("dateoccured")
            if not created:
                raise ValueError("ticket creation timestamp is missing")
            if timestamp(created) >= activated:
                self.store.enroll(ticket["id"])
        self.store.set_setting("cursor", now)
        return len(tickets)

    def context(self, ticket, actions, row):
        prior = json.loads(row["context"])
        processed = set(prior.get("processed_client_ids", []))
        # A delivered acknowledgment does not consume unfinished resolution work.
        if prior.get("pending_resolution"):
            processed.discard(prior["pending_resolution"]["confirmation_action_id"])
        incoming = [a for a in actions if a["source"] == "client" and a["id"] not in processed]
        return {"state": row["state"], "previous": prior, "ticket": ticket,
                "actions": actions, "new_client_actions": incoming}

    def plan(self, ticket_id, row):
        ticket, actions = snapshot(self.halo, ticket_id, self.cfg["agent_id"])
        context = self.context(ticket, actions, row)
        current = fingerprint(ticket, actions)
        if ticket.get("closed") or ticket["status_id"] == self.cfg["closed_status_id"]:
            return {"decision": "ignore", "context": "Ticket is already closed."}, ticket, actions, current
        prior = context["previous"]
        if (prior.get("owner") is not None and prior["owner"] != ticket.get("agent_id")):
            return {"decision": "handoff", "context": "Ticket ownership changed; normal technician handling."}, ticket, actions, current
        # Actual human work is takeover; mere automatic initial assignment is not.
        known = set(prior.get("known_agent_action_ids", []))
        human_work = [a for a in actions if a["source"] == "agent" and a["id"] not in known]
        if human_work:
            return {"decision": "handoff", "context": "A technician has acted on this ticket."}, ticket, actions, current
        if row["state"] != "new" and not context["new_client_actions"]:
            return {"decision": "wait", "context": prior.get("summary", "")}, ticket, actions, current
        if current == row["snapshot"]:
            return None, ticket, actions, current
        plan = validate_plan(self.model.decide(context), context, self.cfg)
        return plan, ticket, actions, current

    def fresh(self, ticket_id, baseline_ticket, baseline_actions, allowed_ids):
        ticket, actions = snapshot(self.halo, ticket_id, self.cfg["agent_id"])
        baseline = {a["id"]: a for a in baseline_actions if a["id"] not in allowed_ids}
        now = {a["id"]: a for a in actions if a["id"] not in allowed_ids}
        current_fields = {k: v for k, v in ticket.items() if k != "last_update"}
        original_fields = {k: v for k, v in baseline_ticket.items() if k != "last_update"}
        if now != baseline or current_fields != original_fields:
            raise Changed("ticket or conversation changed during decision")
        return ticket, actions

    def reconcile_operation(self, operation):
        args = json.loads(operation["arguments"])
        ticket_id = operation["ticket_id"]
        if operation["kind"] == "status":
            ticket = self.halo.ticket(ticket_id)
            if ticket.get("status_id") == args["new_status_id"]:
                return {"status_id": args["new_status_id"]}
            return None
        before = set(json.loads(operation["before_ids"]))
        ticket, actions = snapshot(self.halo, ticket_id, self.cfg["agent_id"])
        target = text(args.get("body") or args.get("note"))
        matches = [a for a in actions if a["id"] not in before and
                   a["source"] == "relay" and a["text"] == target and
                   a["private"] == (operation["kind"] == "note")]
        if operation["kind"] == "email":
            matches = [a for a in matches if parseaddr(a["emailto"])[1].lower() == args["to"].lower()]
        if len(matches) == 1:
            return {"action_id": matches[0]["id"]}
        return None

    def dispatch(self, op_id, ticket_id, kind, name, arguments, before_ids):
        existing = self.store.operation(op_id)
        if existing and existing["state"] != "not_attempted":
            if existing["state"] == "verified":
                return json.loads(existing["receipt"])
            receipt = self.reconcile_operation(existing)
            if receipt:
                self.store.receipt(op_id, receipt)
                return receipt
            raise Uncertain("unverified " + kind + " operation; no duplicate send attempted")
        # Preview is read-only, and is completed before the durable dispatch record.
        try:
            self.halo.call(name, **arguments, confirm=False)
        except TicketChangedBeforeWrite:
            raise Changed("ticket changed before preview") from None
        self.store.begin_operation(op_id, ticket_id, kind, arguments, before_ids)
        try:
            self.halo.call(name, **arguments, confirm=True)
        except TicketChangedBeforeWrite:
            self.store.reject_operation(op_id, ticket_id)
            raise Changed("ticket changed before write") from None
        except Exception:
            # Accepted-but-disconnected calls must be read back, never repeated.
            pass
        operation = self.store.operation(op_id)
        receipt = self.reconcile_operation(operation)
        if receipt:
            self.store.receipt(op_id, receipt)
            return receipt
        raise Uncertain("unverified " + kind + " operation; inspect Halo delivery")

    def execute(self, ticket_id, bundle):
        plan, baseline, actions, digest = (bundle[k] for k in ("plan", "ticket", "actions", "digest"))
        decision = plan["decision"]
        allowed = set()
        prefix = f"{ticket_id}:{digest}"
        pending = json.loads(self.store.ticket(ticket_id)["context"]).get("pending_resolution")
        if decision == "resolve" and pending and pending["confirmation_action_id"] == plan["confirmation_action_id"]:
            # Reuse the original journal, including receipts created before restart.
            prefix = pending["operation_prefix"]
        # A recovered plan may already have verified writes before its crash.
        for kind in ("email", "note"):
            op = self.store.operation(prefix + ":" + kind)
            if op and op["state"] != "not_attempted":
                receipt = json.loads(op["receipt"]) if op["state"] == "verified" else self.reconcile_operation(op)
                if receipt:
                    self.store.receipt(op["id"], receipt)
                    allowed.add(receipt["action_id"])
                    if kind == "email":
                        # The receipt may have committed just before a crash, while
                        # conversation progress did not. Preserve the sent reply
                        # before a new client action can invalidate this old plan.
                        reply_state = {"offer": "offered", "decline": "handed_off",
                                       "handoff": "handed_off"}.get(decision, "troubleshooting")
                        self.progress(ticket_id, bundle, reply_state)
                    elif decision == "resolve":
                        self.progress(ticket_id, bundle, "troubleshooting")
                else:
                    raise Uncertain("previous " + kind + " operation needs readback")
        status_op = self.store.operation(prefix + ":status")
        if status_op and status_op["state"] != "not_attempted":
            receipt = self.reconcile_operation(status_op)
            if receipt:
                self.store.receipt(status_op["id"], receipt)
                self.finish(ticket_id, bundle, "resolved")
                return
            raise Uncertain("previous closure needs readback")
        ticket, current_actions = self.fresh(ticket_id, baseline, actions, allowed)
        email_op = self.store.operation(prefix + ":email")
        if plan.get("reply") and not (email_op and email_op["state"] == "verified"):
            email = parseaddr(str(ticket.get("user_email", "")))[1]
            if not email:
                raise ValueError("ticket contact has no email address")
            outcome = self.halo.call("ticket_outcomes.get", outcome_id=self.cfg["email_outcome_id"],
                                     ticket_id=ticket_id)["result"]["item"]
            if outcome.get("newstatus", 0) not in (0, -1, ticket["status_id"]):
                raise ValueError("email outcome changes ticket status")
            body = email_html(plan["reply"])
            args = {"ticket_id": ticket_id, "outcome_id": self.cfg["email_outcome_id"],
                    "expected_last_update": ticket["last_update"], "to": email,
                    "subject": self.cfg["email_subject_template"].format(
                        ticket_id=ticket_id, summary=ticket.get("summary", "")), "body": body}
            if self.cfg.get("email_template_id"):
                args["email_template_id"] = self.cfg["email_template_id"]
            receipt = self.dispatch(prefix + ":email", ticket_id, "email", "ticket_actions.send_email",
                                    args, [a["id"] for a in current_actions])
            allowed.add(receipt["action_id"])
            # A new client reply can arrive before the later internal note. Persist
            # the completed reply now so replanning cannot repeat the invitation.
            reply_state = {"offer": "offered", "decline": "handed_off", "handoff": "handed_off"}.get(
                decision, "troubleshooting")
            self.progress(ticket_id, bundle, reply_state)
        note = plan.get("private_note", "").strip()
        if decision == "resolve":
            note += f"\nClient confirmation: action {plan['confirmation_action_id']}: {plan['confirmation_quote']}"
        if note:
            if plan["sources"]:
                note += "\nDocumentation: " + ", ".join(plan["sources"])
            note += "\nITECS RELAY operation: " + prefix
            ticket, current_actions = self.fresh(ticket_id, baseline, actions, allowed)
            receipt = self.dispatch(prefix + ":note", ticket_id, "note", "ticket_actions.create_private_note",
                                    {"ticket_id": ticket_id, "note": note},
                                    [a["id"] for a in current_actions])
            allowed.add(receipt["action_id"])
            if decision == "resolve":
                self.progress(ticket_id, bundle, "troubleshooting")
        if decision == "resolve":
            ticket, current_actions = self.fresh(ticket_id, baseline, actions, allowed)
            statuses = self.halo.statuses(ticket_id)
            if not any(s["id"] == self.cfg["closed_status_id"] for s in statuses):
                raise ValueError("configured closed status is not currently allowed")
            self.dispatch(prefix + ":status", ticket_id, "status", "tickets.update_status",
                          {"ticket_id": ticket_id, "expected_current_status_id": ticket["status_id"],
                           "new_status_id": self.cfg["closed_status_id"]},
                          [a["id"] for a in current_actions])
        state = {"offer": "offered", "instructions": "troubleshooting", "clarify": "troubleshooting",
                 "wait": self.store.ticket(ticket_id)["state"], "decline": "handed_off",
                 "handoff": "handed_off", "resolve": "resolved", "ignore": "ignored"}[decision]
        self.finish(ticket_id, bundle, state)

    def finish(self, ticket_id, bundle, state):
        self.progress(ticket_id, bundle, state)
        self.store.save(ticket_id, plan=None, snapshot=bundle["digest"], failures=0,
                        error=None, due=time.time() + self.cfg["poll_seconds"])

    def progress(self, ticket_id, bundle, state):
        previous = json.loads(self.store.ticket(ticket_id)["context"])
        pending_resolution = None
        if bundle["plan"]["decision"] == "resolve" and state != "resolved":
            pending_resolution = previous.get("pending_resolution")
            if not pending_resolution or pending_resolution["confirmation_action_id"] != bundle["plan"]["confirmation_action_id"]:
                pending_resolution = {"confirmation_action_id": bundle["plan"]["confirmation_action_id"],
                                      "operation_prefix": f"{ticket_id}:{bundle['digest']}"}
        self.store.save(ticket_id, state=state, context=json.dumps({
                            "manually_enrolled": previous.get("manually_enrolled", False),
                            "known_agent_action_ids": previous.get("known_agent_action_ids", []),
                            "owner": bundle["ticket"].get("agent_id"),
                            "summary": bundle["plan"].get("context", ""),
                            "pending_resolution": pending_resolution,
                            "processed_client_ids": [a["id"] for a in bundle["actions"] if a["source"] == "client"],
                            "sources": bundle["plan"].get("sources", previous.get("sources", []))}))

    def one(self, ticket_id, inspect=False):
        row = self.store.ticket(ticket_id) or {"state": "new", "context": "{}", "snapshot": "", "plan": None}
        if row["plan"]:
            bundle = json.loads(row["plan"])
        else:
            plan, ticket, actions, digest = self.plan(ticket_id, row)
            if plan is None:
                if not inspect:
                    self.store.save(ticket_id, due=time.time() + self.cfg["poll_seconds"],
                                    failures=0, error=None)
                return None
            bundle = {"plan": plan, "ticket": ticket, "actions": actions, "digest": digest}
        if inspect:
            return bundle
        self.store.save(ticket_id, plan=json.dumps(bundle))
        self.execute(ticket_id, bundle)
        return bundle["plan"]["decision"]
