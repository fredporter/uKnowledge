import json
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer
from aiohttp.web import Application

from uknowledge.routes import register_routes


@pytest.fixture
async def client(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("UDOS_HOME", str(tmp_path / ".udos"))
    monkeypatch.setenv("UDOS_PUBLIC_ROOT", str(tmp_path / "Public"))
    monkeypatch.setenv("UDOS_USER_VAULT_ROOT", str(tmp_path / "Vault"))
    monkeypatch.setenv("UDOS_SHARED_ROOT", str(tmp_path / "Shared"))
    app = Application()
    register_routes(app)
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


async def test_register_public_workspace_marks_it_read_only(client, tmp_path: Path):
    response = await client.post(
        "/api/knowledge/workspaces",
        json={
            "workspace_id": "global",
            "name": "Global Knowledge",
            "vault_path": str(tmp_path / "Public" / "global-knowledge"),
        },
    )

    assert response.status == 201
    assert (await response.json())["permissions"] == "read_only"
    registry = json.loads(
        (tmp_path / ".udos" / "knowledge" / "vault_workspaces.json").read_text()
    )
    assert registry[0]["permissions"] == "read_only"


async def test_create_view_rejects_read_only_workspace(client, tmp_path: Path):
    await client.post(
        "/api/knowledge/workspaces",
        json={
            "workspace_id": "global",
            "name": "Global Knowledge",
            "vault_path": str(tmp_path / "Public" / "global-knowledge"),
        },
    )

    response = await client.post(
        "/api/knowledge/views",
        json={"workspace_id": "global", "title": "Direct mutation"},
    )

    assert response.status == 403
    assert (await response.json())["error"] == "Knowledge workspace is read-only"


async def test_create_view_keeps_writable_workspace_contract(client, tmp_path: Path):
    await client.post(
        "/api/knowledge/workspaces",
        json={
            "workspace_id": "main",
            "name": "Main",
            "vault_path": str(tmp_path / "Vault"),
        },
    )

    response = await client.post(
        "/api/knowledge/views",
        json={"workspace_id": "main", "title": "Research note"},
    )

    assert response.status == 501


async def test_filesystem_documents_and_content_are_served(client, tmp_path: Path):
    note = tmp_path / "Vault" / "guides" / "offline.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Offline First\n\nKeep knowledge local.", encoding="utf-8")

    response = await client.get("/api/knowledge/documents?workspace_id=main")
    payload = await response.json()
    assert response.status == 200
    assert payload["count"] == 1
    document = payload["documents"][0]
    assert document["rel_path"] == "guides/offline.md"
    assert document["permissions"] == "read_write"

    response = await client.get(f"/api/knowledge/documents/{document['id']}/content")
    assert response.status == 200
    assert "Keep knowledge local" in (await response.json())["content"]


async def test_search_is_offline_and_can_scope_to_public(client, tmp_path: Path):
    public_note = tmp_path / "Public" / "global-knowledge" / "water.md"
    public_note.parent.mkdir(parents=True)
    public_note.write_text("# Water\n\nPurification by boiling.", encoding="utf-8")
    private_note = tmp_path / "Vault" / "water.md"
    private_note.parent.mkdir(parents=True)
    private_note.write_text("# Water bill", encoding="utf-8")

    response = await client.get("/api/knowledge/search?q=purification&workspace_id=public")
    payload = await response.json()
    assert response.status == 200
    assert payload["count"] == 1
    assert payload["results"][0]["permissions"] == "read_only"


async def test_document_id_cannot_be_used_for_workspace_escape(client, tmp_path: Path):
    note = tmp_path / "Vault" / "inside.md"
    note.parent.mkdir(parents=True)
    note.write_text("inside", encoding="utf-8")
    documents = (await (await client.get("/api/knowledge/documents?workspace_id=main")).json())["documents"]

    response = await client.get(
        f"/api/knowledge/documents/{documents[0]['id']}?workspace_id=public"
    )
    assert response.status == 404
