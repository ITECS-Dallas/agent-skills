# Server-Only Auth

Use this pattern when browser UI needs data from a privileged service.

## Shape

1. Browser component calls a same-origin route or action.
2. Server route reads session/auth state with server-only helpers.
3. Server route validates params and body.
4. Server route calls upstream service with the privileged token.
5. Server route normalizes status and response shape.

## Route Handler Checklist

- Reject unauthenticated requests with `401`.
- Reject authenticated but unauthorized requests with `403`.
- Validate all path params, query params, and body fields before upstream calls.
- Preserve safe upstream `4xx` messages only when intended.
- Strip upstream internals from `5xx` responses.
- Avoid returning raw upstream response bodies blindly.

## Client Checklist

- Treat `response.json()` as unknown.
- Parse or validate before rendering.
- Handle loading, empty, unavailable, and error states intentionally.
- Do not store privileged tokens in client state.
