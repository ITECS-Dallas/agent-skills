# Frontend Code Generation

Use the repo's canonical generator when API or protocol contracts change.

## Discovery

Search for:

- OpenAPI, GraphQL, protobuf, or typed RPC specs
- `openapi-typescript`, `graphql-codegen`, `protoc`, `buf`, `orval`, or similar tools
- package scripts containing `generate`, `codegen`, `schema`, or `types`
- generated file headers that say not to edit manually

## Rules

- Update the canonical contract first.
- Regenerate generated files instead of hand-editing them.
- Include generated output in the same change when the repo normally commits it.
- Run drift checks if the repo provides them.
- Update consumers and tests in the same branch.

## Fallback

If the repo has no generator, document that fact and prefer a narrow typed parser near the API client over broad global handwritten DTO copies.
