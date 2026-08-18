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
