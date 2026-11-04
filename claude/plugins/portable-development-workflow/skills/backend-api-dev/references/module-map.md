# Backend Module Map

Use this as a discovery checklist. Replace it with the target repo's actual paths after inspection.

## Common Surfaces

- API contracts: `api/`, `openapi/`, `schema/`, `proto/`, `graphql/`
- Entrypoints: `cmd/`, `server/`, `app/`, `main.*`, framework route registries
- Handlers/controllers: `handlers/`, `controllers/`, `routes/`
- Services/use cases: `service/`, `services/`, `domain/`, `usecases/`
- Persistence: `models/`, `repositories/`, `db/`, `migrations/`, `sql/`
- Auth: `auth/`, `middleware/`, `permissions/`, `policies/`
- Tests: colocated tests, `tests/`, package-level test suites

## Mapping Steps

1. Find the public route or job entrypoint.
2. Trace validation and auth.
3. Trace service ownership.
4. Trace persistence or external integration calls.
5. Find the nearest existing tests for each touched layer.
6. Update the narrowest layer that owns the behavior.
