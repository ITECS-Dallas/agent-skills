# Backend Code Generation Targets

## Discovery

Search manifests and scripts for:

- `generate`
- `codegen`
- `openapi`
- `graphql`
- `proto`
- `buf`
- `swagger`
- `schema`
- `migrate`

## Rules

- Do not hand-edit generated files unless the repo explicitly does so.
- Keep generated server stubs, clients, and docs in the same change as the contract.
- Run drift checks if the repo provides them.
- If a consumer repo uses the changed contract, update that consumer in the same branch or document the coordinated follow-up.

## Output Checklist

- canonical spec updated
- generated server surface updated
- generated client surface updated when committed
- handler/service implementation updated
- tests updated at changed boundaries
- docs updated if behavior changed
