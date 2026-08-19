"""Filesystem and permission policy for uKnowledge."""

from __future__ import annotations

import os
from pathlib import Path


def udos_root() -> Path:
    """Return the detachable uDos source/runtime root."""
    explicit = os.environ.get("UDOS_ROOT")
    return Path(explicit).expanduser() if explicit else Path.home() / "Code"


def udos_home() -> Path:
    """Return the canonical mutable ecosystem-state directory."""
    explicit = os.environ.get("UDOS_HOME")
    return Path(explicit).expanduser() if explicit else udos_root() / ".udos"


def public_root() -> Path:
    explicit = os.environ.get("UDOS_PUBLIC_ROOT")
    return Path(explicit).expanduser() if explicit else Path.home() / "Public"


def user_vault_root() -> Path:
    explicit = os.environ.get("UDOS_USER_VAULT_ROOT")
    return Path(explicit).expanduser() if explicit else Path.home() / "Vault"


def shared_root() -> Path:
    explicit = os.environ.get("UDOS_SHARED_ROOT")
    return Path(explicit).expanduser() if explicit else Path.home() / "Shared"


def global_knowledge_root() -> Path:
    explicit = os.environ.get("UKNOWLEDGE_GLOBAL_ROOT")
    return (
        Path(explicit).expanduser()
        if explicit
        else public_root() / "global-knowledge"
    )


def workspace_registry_path() -> Path:
    return udos_home() / "knowledge" / "vault_workspaces.json"


def is_within(path: Path, root: Path) -> bool:
    """Return whether a resolved path is root itself or one of its descendants."""
    try:
        path.expanduser().resolve().relative_to(root.expanduser().resolve())
    except ValueError:
        return False
    return True


def workspace_permissions(path: str | Path) -> str:
    """Classify installed Public vaults as read-only; other vaults are writable."""
    candidate = Path(path).expanduser()
    return "read_only" if is_within(candidate, public_root()) else "read_write"
