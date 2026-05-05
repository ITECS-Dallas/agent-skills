# Conversion Notes

This repo contains a project-neutral rewrite of a previously project-specific development skill bundle.

## Conversion Goals

- Preserve the useful engineering behaviors.
- Remove product names, private paths, fixed repo names, and fixed runtime assumptions.
- Rename project-specific frontend and backend skills into generic reusable skills.
- Keep orchestration explicit so agents can load only the skills relevant to a task.
- Add validation so project-specific terms do not drift back in.

## Resulting Structure

- Frontend-specific guidance lives in `frontend-app-dev`.
- Backend/API-specific guidance lives in `backend-api-dev`.
- Cross-boundary verification lives in `backend-boundary-testing`.
- General delivery, docs, PR, reuse, and quality gates remain as independent skills.
- `project-development-workflow` ties the catalog together without assuming a particular stack.

## Project-Specific Customization

Do not edit these skills to add one project's paths or commands. Instead, put local details in that project's `AGENTS.md`, `CLAUDE.md`, or repo-local docs, and let these skills reference those local docs when the project provides them.
