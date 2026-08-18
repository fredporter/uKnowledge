from pathlib import Path

from uknowledge.config import (
    global_knowledge_root,
    udos_home,
    workspace_permissions,
    workspace_registry_path,
)


def test_mutable_state_defaults_below_udos_root(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("UDOS_ROOT", str(tmp_path / "Code"))
    monkeypatch.delenv("UDOS_HOME", raising=False)

    assert udos_home() == tmp_path / "Code" / ".udos"
    assert workspace_registry_path() == (
        tmp_path / "Code" / ".udos" / "knowledge" / "vault_workspaces.json"
    )


def test_global_knowledge_defaults_to_public(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("UDOS_PUBLIC_ROOT", str(tmp_path / "Public"))
    monkeypatch.delenv("UKNOWLEDGE_GLOBAL_ROOT", raising=False)

    assert global_knowledge_root() == tmp_path / "Public" / "global-knowledge"


def test_public_vaults_are_read_only(monkeypatch, tmp_path: Path):
    public = tmp_path / "Public"
    monkeypatch.setenv("UDOS_PUBLIC_ROOT", str(public))

    assert workspace_permissions(public / "global-knowledge") == "read_only"
    assert workspace_permissions(public / "addon-vault") == "read_only"
    assert workspace_permissions(tmp_path / "Vault") == "read_write"

