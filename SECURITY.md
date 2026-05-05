# Security

This repository must stay safe to clone into any project or workstation.

## Do Not Commit

- API keys, OAuth tokens, SSH keys, cookies, session files, or `.env` values.
- Client, customer, employee, or production data.
- Absolute private filesystem paths.
- Host-specific service names, IP allowlists, VPN details, or deployment secrets.

## Safe Skill Content

Skills may include:

- Project-neutral workflow guidance.
- Placeholder commands with obvious variables.
- Scripts that operate only on the current checkout or explicit install targets.
- Templates that require local replacement before use.

Skills must not include:

- Live credentials.
- Hidden network calls.
- Commands that mutate production systems by default.
- Project-specific facts that belong in a project repo.

## Reporting Issues

If a secret or private project detail is committed, rotate the exposed secret first, then remove it from history before wider reuse.
