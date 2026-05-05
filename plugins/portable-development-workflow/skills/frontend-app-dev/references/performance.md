# Frontend Performance

## Before Editing

- Identify whether the touched code is in a shared shell, route, or leaf component.
- Inspect the current build or bundle report if available.
- Note whether the route is static, request-time, or client-rendered.

## Guardrails

- Keep client-only code at the smallest interactive leaf.
- Avoid adding large dependencies to shared shells.
- Prefer route-level loading boundaries for slow data.
- Use framework image and font primitives when available.
- Avoid layout shifts by setting stable dimensions for media and fixed-format UI.
- Do not add polling or immediate refetches without a freshness reason.

## Validate

- Run the production build when route structure, framework config, or shared shell changed.
- Use browser tests or screenshots for layout-sensitive changes.
- Compare mobile and desktop when public pages or responsive behavior changed.
