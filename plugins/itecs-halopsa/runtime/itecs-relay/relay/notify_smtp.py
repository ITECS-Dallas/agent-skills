#!/usr/bin/python3
"""US1 operational mail helper; install this file root-owned before configuring it.

Reuses Seafile's existing SMTP account without importing its application settings.
The recipient and message vocabulary are fixed; no client body is accepted.
"""

import argparse
import ast
from email.message import EmailMessage
import json
from pathlib import Path
import smtplib
import ssl
import sys


SETTINGS = Path("/opt/seafile-data/seafile/conf/seahub_settings.py")
RECIPIENT = "notifications@itecsonline.com"
CODES = {
    "health_check_failed": "RELAY health could not be read; inspect the worker configuration and state database.",
    "service_not_running": "The RELAY service is stopped.",
    "service_heartbeat_stale": "The RELAY service has stopped reporting progress.",
    "discovery_error": "RELAY cannot discover new Halo tickets.",
    "discovery_stale": "RELAY has not completed a recent intake scan.",
    "write_needs_readback": "A Halo write needs technician readback before resuming.",
    "ticket_processing_error": "RELAY encountered a ticket processing error and is retrying.",
    "ticket_job_stale": "A ticket processing job has exceeded its expected duration.",
}


def smtp_settings(path):
    required = {"EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD",
                "EMAIL_USE_TLS", "DEFAULT_FROM_EMAIL"}
    values = {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in required:
                    values[target.id] = ast.literal_eval(node.value)
    if set(values) != required or values["EMAIL_USE_TLS"] is not True:
        raise ValueError("Expected literal authenticated STARTTLS settings are unavailable")
    return values


def message(health, sender):
    if type(health.get("healthy")) is not bool or not isinstance(health.get("issues"), list):
        raise ValueError("Expected structured health report")
    if health["healthy"] != (not health["issues"]):
        raise ValueError("Health state and issues disagree")
    lines = []
    for issue in health["issues"]:
        line = CODES.get(issue["code"], "RELAY reported an unrecognized health condition; verify monitor and notification-helper versions.")
        if "ticket_id" in issue:
            if type(issue["ticket_id"]) is not int or issue["ticket_id"] <= 0:
                raise ValueError("Invalid ticket ID")
            line = f"Ticket {issue['ticket_id']}: " + line
        lines.append(line)
    mail = EmailMessage()
    mail["From"] = sender
    mail["To"] = RECIPIENT
    mail["Subject"] = "ITECS RELAY recovered" if health["healthy"] else "ITECS RELAY needs attention"
    mail["Auto-Submitted"] = "auto-generated"
    mail["X-Auto-Response-Suppress"] = "All"
    body = "ITECS RELAY on US1 (.92)\n\n"
    body += "\n".join(lines) if lines else "All previously reported RELAY health issues have cleared."
    body += ("\n\nThe normal Halo technician queue remains available. For details, inspect "
             "RELAY status and its service journal on US1. For an uncertain write, "
             "review the Halo action before using RELAY resume.\n")
    mail.set_content(body)
    return mail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="authenticate without sending email")
    args = parser.parse_args()
    try:
        settings = smtp_settings(SETTINGS)
        health = None if args.check else json.loads(sys.stdin.read(32768))
        mail = None if args.check else message(health, settings["DEFAULT_FROM_EMAIL"])
        with smtplib.SMTP(settings["EMAIL_HOST"], settings["EMAIL_PORT"], timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(settings["EMAIL_HOST_USER"], settings["EMAIL_HOST_PASSWORD"])
            if mail is not None and smtp.send_message(mail):
                raise RuntimeError("SMTP recipient rejected")
        print(json.dumps({"smtp_authenticated": True, "email_sent": mail is not None}))
        return 0
    except Exception as exc:
        # SMTP/provider messages can contain addresses or credential details.
        print(json.dumps({"error": type(exc).__name__}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
