"""Filesystem-first Markdown knowledge library.

The filesystem is authoritative.  This module deliberately has no dependency on
uCore, AppFlowy, an embedding service, or a running model.
"""

from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import (
    public_root,
    shared_root,
    user_vault_root,
    workspace_permissions,
    workspace_registry_path,
)

_EXCLUDED_PARTS = {".git", ".obsidian", ".trash", "node_modules", "__pycache__", "_site", "_compost"}
_WORDS = re.compile(r"[a-z0-9]+")


def _registry() -> list[dict[str, Any]]:
    path = workspace_registry_path()
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def list_workspaces() -> list[dict[str, Any]]:
    builtins = (
        ("main", "Main Vault", user_vault_root(), "user"),
        ("shared", "Shared Vaults", shared_root(), "shared"),
        ("public", "Public Knowledge", public_root(), "public"),
    )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for workspace_id, name, path, source in builtins:
        rows.append(_workspace_row(workspace_id, name, path, source))
        seen.add(workspace_id)
    for item in _registry():
        workspace_id = str(item.get("workspace_id") or item.get("id") or "").strip()
        path_text = str(item.get("vault_path") or item.get("path") or "").strip()
        if not workspace_id or not path_text or workspace_id in seen:
            continue
        rows.append(_workspace_row(workspace_id, str(item.get("name") or workspace_id), Path(path_text), str(item.get("source") or "registered")))
        seen.add(workspace_id)
    return rows


def _workspace_row(workspace_id: str, name: str, path: Path, source: str) -> dict[str, Any]:
    path = path.expanduser()
    return {
        "id": workspace_id,
        "workspace_id": workspace_id,
        "name": name,
        "icon": None,
        "member_count": 0,
        "source": source,
        "path": str(path),
        "vault_path": str(path),
        "exists": path.is_dir(),
        "permissions": workspace_permissions(path),
    }


def _workspace(workspace_id: str) -> dict[str, Any] | None:
    return next((row for row in list_workspaces() if row["id"] == workspace_id), None)


def _documents(workspace_id: str | None = None) -> Iterator[tuple[dict[str, Any], Path, str]]:
    workspaces = [_workspace(workspace_id)] if workspace_id else list_workspaces()
    seen: set[Path] = set()
    for workspace in workspaces:
        if not workspace:
            continue
        root = Path(str(workspace["path"])).expanduser().resolve()
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.md")):
            if any(part in _EXCLUDED_PARTS or part.startswith(".") for part in path.relative_to(root).parts):
                continue
            resolved = path.resolve()
            if resolved in seen or not resolved.is_file() or not resolved.is_relative_to(root):
                continue
            seen.add(resolved)
            yield workspace, resolved, resolved.relative_to(root).as_posix()


def _object_id(workspace_id: str, relative_path: str) -> str:
    payload = f"{workspace_id}\0{relative_path}".encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def _decode_object_id(object_id: str) -> tuple[str, str] | None:
    try:
        raw = base64.urlsafe_b64decode(object_id + "=" * (-len(object_id) % 4)).decode()
        workspace_id, relative_path = raw.split("\0", 1)
    except (ValueError, UnicodeDecodeError):
        return None
    return workspace_id, relative_path


def _resolve(object_id: str, workspace_id: str | None = None) -> tuple[dict[str, Any], Path, str] | None:
    decoded = _decode_object_id(object_id)
    if not decoded:
        return None
    encoded_workspace, relative_path = decoded
    if workspace_id and encoded_workspace != workspace_id:
        return None
    workspace = _workspace(encoded_workspace)
    if not workspace:
        return None
    root = Path(str(workspace["path"])).expanduser().resolve()
    candidate = (root / relative_path).resolve()
    if candidate.suffix.lower() != ".md" or not candidate.is_file() or not candidate.is_relative_to(root):
        return None
    return workspace, candidate, candidate.relative_to(root).as_posix()


def _metadata(workspace: dict[str, Any], path: Path, relative_path: str) -> dict[str, Any]:
    stat = path.stat()
    return {
        "id": _object_id(str(workspace["id"]), relative_path),
        "object_id": _object_id(str(workspace["id"]), relative_path),
        "title": path.stem,
        "type": "markdown",
        "updated_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "workspace_id": workspace["id"],
        "source": workspace["source"],
        "rel_path": relative_path,
        "path": str(path),
        "data_size": stat.st_size,
        "permissions": workspace["permissions"],
    }


def list_documents(workspace_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    return [_metadata(*entry) for entry in list(_documents(workspace_id))[: max(1, min(limit, 1000))]]


def get_document(object_id: str, workspace_id: str | None = None) -> dict[str, Any] | None:
    resolved = _resolve(object_id, workspace_id)
    return _metadata(*resolved) if resolved else None


def get_document_content(object_id: str, workspace_id: str | None = None) -> str | None:
    resolved = _resolve(object_id, workspace_id)
    if not resolved:
        return None
    try:
        return resolved[1].read_text(encoding="utf-8", errors="replace")[:1_000_000]
    except OSError:
        return None


def search(query: str, workspace_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    terms = _WORDS.findall(query.lower())
    if not terms:
        return []
    ranked: list[tuple[int, dict[str, Any]]] = []
    for workspace, path, relative_path in _documents(workspace_id):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        title = path.stem.lower()
        body = content.lower()
        if not all(term in title or term in body for term in terms):
            continue
        score = sum(title.count(term) * 10 + body.count(term) for term in terms)
        row = _metadata(workspace, path, relative_path)
        row.update({"content": content[:500], "score": score})
        ranked.append((score, row))
    ranked.sort(key=lambda item: (-item[0], str(item[1]["rel_path"])))
    return [row for _, row in ranked[: max(1, min(limit, 100))]]
