# uKnowledge — Offline Knowledge Engine

Offline corpus, vault indexing, search, packaging, provenance, and contribution
contracts extracted from uCore.

## Status: Stabilizing Split-Repo Ownership

uKnowledge is now the required owner for knowledge route registration.
uCore delegates route registration to `uknowledge.routes.register_routes(app)`.
Core read/query endpoints still use a temporary AppFlowy compatibility bridge. The
next extraction replaces that dependency with filesystem-first offline reading and
search. Remaining mutation and sync paths are explicit not-yet-implemented
contracts rather than silent fallbacks.

## Permission model

- Installed Public vaults, including `~/Public/global-knowledge`, are read-only in
  normal user mode.
- BrowserUI and user workflows write research into user-owned or explicitly selected
  writable vaults.
- Global Knowledge changes are contribution packages. Only an authorized
  Dev/maintainer workflow may accept them into the canonical candidate corpus and
  publish a validated edition.
- Mutable registries and indexes live under `UDOS_HOME` (default
  `~/Code/.udos/knowledge`), never in `~/.ucore` or a Public vault.

## Architecture

```
uKnowledge (this repo)        uCore (host)
┌────────────────────────┐   ┌──────────────────────────────┐
│ routes + policy        │◄──│ extension registry           │
│ (external ownership)   │   │   import uknowledge.routes   │
│ /api/knowledge/*       │   │   fail-fast if missing       │
└────────────────────────┘   └──────────────────────────────┘
```

## Endpoints

| Method | Path                                         | Description         |
| ------ | -------------------------------------------- | ------------------- |
| GET    | `/api/knowledge/workspaces`                  | AppFlowy workspaces |
| GET    | `/api/knowledge/documents`                   | List documents      |
| GET    | `/api/knowledge/documents/{id}`              | Single document     |
| GET    | `/api/knowledge/documents/{id}/content`      | Document content    |
| GET    | `/api/knowledge/search`                      | Semantic search     |
| GET    | `/api/knowledge/adapter/mission-task-binder` | Task binder         |
| GET    | `/api/knowledge/local/databases`             | Local DB discovery  |
| GET    | `/api/knowledge/local/tables`                | List tables         |
| POST   | `/api/knowledge/local/query`                 | Run SQL query       |
| POST   | `/api/knowledge/local/export`                | Export to vault     |
| POST   | `/api/knowledge/import`                      | AF import           |
| POST   | `/api/knowledge/sync`                        | AF sync             |
| GET    | `/api/knowledge/status`                      | AF status           |
| GET    | `/api/knowledge/index/status`                | Index status        |
| GET    | `/api/knowledge/import/status`               | Import job status   |
| GET    | `/api/knowledge/index/coverage`              | Coverage stats      |

Current behavior:

- `/api/knowledge/workspaces`: implemented (returns 200)
- `/api/knowledge/documents`: implemented (returns 200)
- `/api/knowledge/documents/{id}`: implemented (returns 200/404)
- `/api/knowledge/documents/{id}/content`: implemented (returns 200/404)
- `/api/knowledge/search`: implemented (returns 400 for missing `q`, else 200)
- all other routes: temporary `501` with payload
  `{ "error": "Not implemented in uKnowledge yet", "endpoint": "<route>" }`

## Extension Manifest

```json
{
  "id": "uknowledge",
  "name": "uKnowledge Bridge",
  "kind": "knowledge",
  "version": "0.1.0",
  "optional": false,
  "api_prefix": "/api/knowledge",
  "entrypoint": "uknowledge.setup",
  "route_registrar": "uknowledge.routes.register_routes",
  "dependencies": ["ucore-core"]
}
```

## License

Apache 2.0
