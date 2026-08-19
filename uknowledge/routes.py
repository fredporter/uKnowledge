"""uKnowledge route registrar."""

from __future__ import annotations

import json
from pathlib import Path

from aiohttp import web

from .config import workspace_permissions, workspace_registry_path
from .library import (
    get_document,
    get_document_content,
    list_documents,
    list_workspaces,
    search,
)


async def handle_list_workspaces(_request: web.Request) -> web.Response:
    """GET /api/knowledge/workspaces — list filesystem vaults."""
    workspaces = list_workspaces()
    return web.json_response(
        {"workspaces": workspaces, "count": len(workspaces)},
    )


async def handle_list_documents(request: web.Request) -> web.Response:
    """GET /api/knowledge/documents — list documents in a workspace."""
    workspace_id = request.query.get("workspace_id")
    docs = list_documents(workspace_id)
    return web.json_response(
        {"documents": docs, "count": len(docs)},
    )


async def handle_get_document(request: web.Request) -> web.Response:
    """GET /api/knowledge/documents/{object_id} — get document metadata."""
    object_id = request.match_info.get("object_id", "").strip()
    workspace_id = request.query.get("workspace_id")
    doc = get_document(object_id, workspace_id)
    if not doc:
        return web.json_response({"error": "Document not found"}, status=404)
    return web.json_response(doc)


async def handle_get_document_content(request: web.Request) -> web.Response:
    """GET /api/knowledge/documents/{object_id}/content — get document text."""
    object_id = request.match_info.get("object_id", "").strip()
    workspace_id = request.query.get("workspace_id")
    content = get_document_content(object_id, workspace_id)
    if content is None:
        return web.json_response({"error": "Document not found"}, status=404)
    return web.json_response(
        {"object_id": object_id, "content": content, "length": len(content)},
    )


def _workspace_registry_path() -> Path:
    """Compatibility wrapper for callers/tests using the historical helper."""
    return workspace_registry_path()


def _load_workspace_registry() -> list[dict[str, object]]:
    path = _workspace_registry_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _save_workspace_registry(items: list[dict[str, object]]) -> None:
    path = _workspace_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")


async def handle_register_workspace(request: web.Request) -> web.Response:
    """POST /api/knowledge/workspaces — register a vault workspace mapping."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    workspace_id = str(body.get("workspace_id") or "").strip()
    name = str(body.get("name") or "").strip()
    vault_path = str(body.get("vault_path") or "").strip()

    if not workspace_id or not name:
        return web.json_response(
            {"error": "workspace_id and name are required"},
            status=400,
        )

    permissions = workspace_permissions(vault_path) if vault_path else "read_write"
    rows = _load_workspace_registry()
    rows = [r for r in rows if str(r.get("workspace_id")) != workspace_id]
    rows.append(
        {
            "workspace_id": workspace_id,
            "name": name,
            "vault_path": vault_path,
            "source": "udos-vaults",
            "permissions": permissions,
        },
    )
    _save_workspace_registry(rows)
    return web.json_response(
        {
            "status": "registered",
            "workspace_id": workspace_id,
            "name": name,
            "vault_path": vault_path,
            "permissions": permissions,
        },
        status=201,
    )


async def handle_workspace_views(request: web.Request) -> web.Response:
    """GET /api/knowledge/workspaces/{workspace_id}/views — list docs."""
    workspace_id = request.match_info.get("workspace_id", "").strip() or None
    docs = list_documents(workspace_id)
    return web.json_response(
        {
            "workspace_id": workspace_id,
            "views": docs,
            "count": len(docs),
        },
    )


async def handle_get_view(request: web.Request) -> web.Response:
    """GET /api/knowledge/views/{view_id} — fetch one document/view."""
    view_id = request.match_info.get("view_id", "").strip()
    workspace_id = request.query.get("workspace_id")
    doc = get_document(view_id, workspace_id)
    if not doc:
        return web.json_response({"error": "View not found"}, status=404)
    return web.json_response(doc)


async def handle_create_view(request: web.Request) -> web.Response:
    """POST /api/knowledge/views — create a new document/view.

    This endpoint is an explicit integration point for AppFlowy plugin flows.
    Real creation in AppFlowy is not yet extracted into uKnowledge.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    title = str(body.get("title") or "").strip()
    workspace_id = str(body.get("workspace_id") or "").strip()
    if not title or not workspace_id:
        return web.json_response(
            {"error": "title and workspace_id are required"},
            status=400,
        )

    workspace = next(
        (
            row
            for row in _load_workspace_registry()
            if str(row.get("workspace_id")) == workspace_id
        ),
        None,
    )
    if workspace and workspace.get("permissions") == "read_only":
        return web.json_response(
            {
                "error": "Knowledge workspace is read-only",
                "workspace_id": workspace_id,
            },
            status=403,
        )

    return web.json_response(
        {
            "error": "Not implemented in uKnowledge yet",
            "endpoint": "/api/knowledge/views",
            "workspace_id": workspace_id,
            "title": title,
        },
        status=501,
    )


async def handle_search(request: web.Request) -> web.Response:
    """GET /api/knowledge/search?q=... — offline lexical Markdown search."""
    query = request.query.get("q", "").strip()
    if not query:
        return web.json_response(
            {"error": "q parameter is required"},
            status=400,
        )

    workspace_id = request.query.get("workspace_id")
    try:
        limit = int(request.query.get("limit", "10"))
    except ValueError:
        return web.json_response(
            {"error": "limit must be an integer"},
            status=400,
        )

    results = search(query, workspace_id, limit)
    return web.json_response(
        {"query": query, "results": results, "count": len(results)},
    )


def _not_implemented(path: str):
    async def handler(_request: web.Request) -> web.Response:
        return web.json_response(
            {
                "error": "Not implemented in uKnowledge yet",
                "endpoint": path,
            },
            status=501,
        )

    return handler


def register_routes(app: web.Application) -> None:
    """Register the knowledge surface expected by uCore."""
    routes: list[tuple[str, str]] = [
        ("GET", "/api/knowledge/workspaces"),
        ("POST", "/api/knowledge/workspaces"),
        ("GET", "/api/knowledge/workspaces/{workspace_id}/views"),
        ("GET", "/api/knowledge/documents"),
        ("GET", "/api/knowledge/documents/{object_id}"),
        ("GET", "/api/knowledge/documents/{object_id}/content"),
        ("GET", "/api/knowledge/views/{view_id}"),
        ("POST", "/api/knowledge/views"),
        ("GET", "/api/knowledge/search"),
        ("GET", "/api/knowledge/adapter/mission-task-binder"),
        ("GET", "/api/knowledge/local/databases"),
        ("GET", "/api/knowledge/local/tables"),
        ("POST", "/api/knowledge/local/query"),
        ("POST", "/api/knowledge/local/export"),
        ("POST", "/api/knowledge/import"),
        ("POST", "/api/knowledge/sync"),
        ("GET", "/api/knowledge/status"),
        ("GET", "/api/knowledge/index/status"),
        ("GET", "/api/knowledge/import/status"),
        ("GET", "/api/knowledge/index/coverage"),
    ]

    for method, path in routes:
        if method == "GET":
            if path == "/api/knowledge/search":
                app.router.add_get(path, handle_search)
            elif path == "/api/knowledge/workspaces":
                app.router.add_get(path, handle_list_workspaces)
            elif path == "/api/knowledge/workspaces/{workspace_id}/views":
                app.router.add_get(path, handle_workspace_views)
            elif path == "/api/knowledge/documents":
                app.router.add_get(path, handle_list_documents)
            elif path == "/api/knowledge/documents/{object_id}":
                app.router.add_get(path, handle_get_document)
            elif path == "/api/knowledge/documents/{object_id}/content":
                app.router.add_get(path, handle_get_document_content)
            elif path == "/api/knowledge/views/{view_id}":
                app.router.add_get(path, handle_get_view)
            else:
                app.router.add_get(path, _not_implemented(path))
        elif method == "POST":
            if path == "/api/knowledge/workspaces":
                app.router.add_post(path, handle_register_workspace)
            elif path == "/api/knowledge/views":
                app.router.add_post(path, handle_create_view)
            else:
                app.router.add_post(path, _not_implemented(path))
