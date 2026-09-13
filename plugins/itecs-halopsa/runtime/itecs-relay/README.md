# ITECS RELAY

RELAY watches new HaloPSA ticket intake and conducts the optional client support
conversation through the existing ITECS HaloPSA connector. Python 3.12+ and SQLite
provide the resident service and durable state; `codex exec` uses the runtime
account's saved ChatGPT subscription authentication. There is no LLM API key,
second Halo API client, public webhook endpoint, or separate knowledge database.

## Ownership and operation

- GO-MCP owns this worker and the Halo connector. The `agent-skills` repository
  distributes the worker with `itecs-halopsa` and owns its client workflow skill.
- `/home/itecs/US1` is the working root. The current synchronized library lives at
  `/home/itecs/US1/ATLAS`. `documentation_root` records that observed layout;
  the service does not rename or move the library.
- New tickets are discovered every 15 seconds using Halo's `dateoccured` date
  filter. A persisted cursor and two-minute overlap recover interrupted scans.
  Conversation actions are read completely and deduplicated by ID. Two independent
  decision workers prevent one slow conversation from stopping discovery.
- Activation starts with new intake, rather than emailing an existing backlog.
  The model checks that the ticket is a client email support request and that a
  short relevant procedure exists before offering help. Projects, internal tasks,
  complex requests and monitoring alerts continue through normal handling.
- A client can accept, decline, ask a question, report failure or confirm a fix.
  Failed intermediate steps continue through the applicable procedure. Silence
  does not generate a follow-up or close the ticket. Technician work or a change
  of owner ends Relay's participation.

## Client service policy

Quick automated troubleshooting is complimentary for every client, including
unlimited-support, retainer and hourly clients. RELAY does not decide charges,
deduct retainer hours, create billable time or promise free technician assistance.
Technician work follows the existing service agreement.

Continue relevant clarification, related symptoms and applicable next steps on the
original issue, without an arbitrary message limit. A separate issue requires the
client to submit a new ticket through the client portal or a new support email;
RELAY does not create, split or link it for them. Ask one short question when
relatedness is unclear. If the original is confirmed resolved and a separate issue
is mentioned, acknowledge the fix, direct the client to submit that new ticket,
then record and close the original. Unresolved original issues remain open.

## Decision and delivery

Codex reads the ticket snapshot, conversation state and actual client documents,
then returns structured JSON. The worker sends the email or records the resolution
using the existing typed connector tools and their preview/execute contract.
The operator's authorization for the service covers these defined conversations;
it is supplied to each Codex invocation. No per-reply confirmation is requested.

Every operation is journaled before dispatch and independently read back. A crash
after acceptance is recovered from Halo evidence. A write whose acceptance cannot
be established enters `uncertain`; the service does not repeat that email. An
operator can inspect Halo and use `resume` to recheck the same operation. Resume
retains its journal and cannot erase an uncertain send or force a duplicate.

Before closure, the decision must identify the latest fresh, attributable client
message and quote its confirmation. The worker sends the resolution acknowledgment,
then records actual work and its sources
in a private note, rereads ticket/actions, resolves the configured closed status
against current allowed statuses, closes, and reads back. A contradictory reply or
technician action arriving before closure invalidates the pending plan.

`email_subject_template` preserves the tenant's ticket reference format for inbound
reply matching. The ITECS example uses `[ITECS-0093055]` for ticket 93055. The subject
uses the existing ticket summary; the model cannot choose another ticket reference.

Replies use short HTML paragraphs and actual ordered lists, with escaped plain-text
model content. `email_template_id` optionally selects a Halo template for each RELAY
email; zero or omission retains the action's normal template. Custom Halo template
IDs may be negative. The ITECS-specific template is `ITECS RELAY - Client Support`
(ID -121), containing `$richactionnote`, the original ITECS-SALES PNG logo, RELAY's
contact signature, the complimentary/same-ticket notice and the existing legal
footer. Configure -121 only on the RELAY service. The shared Ticket Update template
(11), Email User outcome (16), mailbox defaults and other agent signatures remain
unchanged. RELAY is API-only, which disables its Preferences tab and excludes it
from Halo's mailbox signature-override picker; a per-message template avoids
changing that account type. Maintain branding in Halo, not in model-written replies.

Halo has no transactional API spanning an incoming client reply and a status
change. The worker narrows that race with immediate action readback and the
connector's current-status check; it cannot provide atomic exactly-once delivery
or claim an email reached the recipient's inbox from API acceptance alone.

## Setup

Install the Linux-capable ITECS HaloPSA plugin first. Its existing command-backed
Automation Vault configuration remains outside the synchronized workspace.
The deployment account needs a working subscription `codex login`, Python 3.12+,
and the installed connector. `codex exec --ignore-user-config` isolates the decision
process from unrelated user-configured MCP integrations while retaining login.

Copy `config.example.json` to `~/.config/itecs-relay/config.json`, mode 0600.
Use actual executable/package paths. Resolve `email_outcome_id` and
`closed_status_id` from the tenant; the zero template values are intentionally
not a deployment configuration. Verify the email outcome leaves the ticket open
and inspect its assignment, timer and workflow effects.

For the reviewed ITECS tenant, agent 49 is ITECSRELAY, outcome 16 is Email User
with `newstatus=-1`, and status 9 is Closed. The external Halo scope includes
`read:tickets edit:tickets read:projects edit:projects all:teams read:customers`.
These are deployment observations, not portable defaults. Exact-ticket action
availability comes from the detailed ticket's `outcomes` array, as in Halo's UI.
The connector preserves the authenticated agent's returned set. A global outcome
catalog does not establish the action is allowed on the current ticket.

From this directory (or the packaged `runtime/itecs-relay` directory):

```bash
python3 -m relay --config ~/.config/itecs-relay/config.json check
python3 -m relay --config ~/.config/itecs-relay/config.json inspect \
  --ticket TICKET_ID --output ~/.local/state/itecs-relay/inspection.json
bash install-user-service.sh ~/.config/itecs-relay/config.json
```

`inspect` performs a read-only decision review and writes a private local artifact;
it neither enrolls the ticket nor sends messages. `check` verifies identity,
required tools and configured documentation paths; it does not certify live email
delivery, every tenant workflow, or available subscription quota.

For an explicitly requested existing-ticket conversation or controlled test, run:

```bash
python3 -m relay --config ~/.config/itecs-relay/config.json process --ticket TICKET_ID
```

This enrolls only the named ticket and performs one decision/delivery cycle. Run it
again after the client replies, or let an activated service continue the enrolled
conversation. Existing technician history is treated as the authorized handoff;
subsequent technician work still ends participation. Repeated `process` calls keep
all previous progress and delivery receipts. It cannot run alongside the resident
worker using the same state directory.

To run an ongoing simulation on that ticket, `serve --ticket TICKET_ID` watches
only the named conversation and does not discover or process other tickets.
Pass the ticket ID as the installer's second argument to persist that mode in the
unit, then enable the service normally. Reinstall without the second argument and
restart when authorizing general new-ticket intake. Client replies still determine
whether to continue, hand off or close; the service does not synthesize replies.

The installer stages the unit without starting client correspondence. Once
deployment is authorized, enable it with:

```bash
systemctl --user enable --now itecs-relay.service
```

The user manager must survive logout and start at boot; on a headless server,
enable lingering for the actual service account with `sudo loginctl enable-linger
itecs`. State, private inspections, SQLite and temporary decision outputs live
under `~/.local/state/itecs-relay`, outside Seafile. The service uses restrictive
file creation permissions. Journal messages contain IDs/status and error classes,
not client bodies or credentials.

On US1, Codex 0.153.4's default bubblewrap sandbox cannot initialize its loopback
interface (`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`). Set
`codex_use_legacy_landlock` to `true` in this host's Relay configuration to select
Codex's available Landlock compatibility implementation. The decision still runs
with `--sandbox read-only`; this is an explicit host setting, not an automatic
retry without a sandbox. Verify actual document reads and denied writes/network
with that installed CLI before enabling the service. The feature is deprecated in
0.153.4, so recheck availability when upgrading Codex. See the official
[Linux permission implementation](https://learn.chatgpt.com/docs/permissions#how-enforcement-works).

## Operate and recover

```bash
python3 -m relay --config ~/.config/itecs-relay/config.json status
journalctl --user -u itecs-relay.service -n 50
systemctl --user stop itecs-relay.service
python3 -m relay --config ~/.config/itecs-relay/config.json resume --ticket TICKET_ID
```

`status` returns nonzero when a ticket or discovery has an error. For Codex failure,
check subscription login/allowance under the same account. For Halo failures,
check vault access, requested scope and current outcome availability. Transient
pre-write failures retain the decision and retry with a bounded delay; they remain
visible in status. Stopping the service leaves the normal Halo queue operational.

## Validation

```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 tests/eval_codex.py \
  --skill /absolute/agent-skills/plugins/itecs-halopsa/skills/service-desk-client-troubleshooting/SKILL.md \
  --output ../../reports/itecs-relay-evals
```

Unit tests cover restart recovery, lost responses, fresh-client attribution,
quoted confirmations, declines, procedural continuation, technician takeover,
pagination, cursor recovery and competing replies. The integration test builds
the real connector and reuses the existing synthetic Atlas tenant. The separate
Codex evaluation uses subscription authentication and fictional documentation;
it consumes normal Codex allowance and does not connect to Halo.

Implementation references: [Codex non-interactive execution](https://learn.chatgpt.com/docs/non-interactive-mode),
the repository's Halo OpenAPI snapshot, and the existing typed MCP contract.
