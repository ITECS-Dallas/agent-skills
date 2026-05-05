# Shared Agent Skills

This project uses shared agent workflow skills from:

`git@github.com:ITECS-Dallas/agent-skills.git`

## Local Refresh

```bash
cd ~/Github/agent-skills
git pull --ff-only
node scripts/validate.mjs
./scripts/install.sh --target both --mode symlink --force
```

## Project-Specific Rules

Keep this project's local facts here:

- repo roots and app boundaries
- local commands
- deployment boundaries
- environment names
- approval gates
- testing requirements

Do not fork the shared skills just to add project-specific paths. Prefer this project file as the local overlay.
