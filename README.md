# uKnowledge — Knowledge Bridge

AppFlowy bridge, semantic search, knowledge layer, and vault indexing extracted from uCore.

## Status: Hard-Cut Ownership (Wave B)

uKnowledge is now the required owner for knowledge route registration.
uCore delegates route registration to `uknowledge.routes.register_routes(app)`.
Core read/query endpoints are live, with remaining mutation and sync paths
still marked as explicit not-yet-implemented contracts.

## Architecture

```
uKnowledge (this repo)        uCore (host)
┌────────────────────────┐   ┌──────────────────────────────┐
│ uknowledge/routes.py   │◄──│ knowledge_adapter.py         │
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
  "route_registrar": "uknowledge.routes.register_routes",
  "dependencies": ["ucore-core"]
}
```

## License

Apache 2.0
