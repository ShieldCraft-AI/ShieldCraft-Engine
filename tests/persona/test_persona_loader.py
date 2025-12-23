import json
import pytest

from shieldcraft.persona import load_persona, PersonaError


def test_valid_persona_loads(monkeypatch, tmp_path):
    # Ensure repo sync check passes
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True})
    # Make worktree appear clean
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)

    persona = {
        "persona_version": "v1",
        "version": "1.0",
        "name": "Fiona",
        "role": "cofounder",
        "scope": ["engineering"],
        "allowed_actions": ["advise"]}
    p = tmp_path / "persona.json"
    p.write_text(json.dumps(persona))

    loaded = load_persona(str(p))
    assert loaded.name == "Fiona"
    assert loaded.role == "cofounder"


def test_invalid_persona_missing_name(monkeypatch, tmp_path):
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True})
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)

    persona = {"role": "cofounder"}
    p = tmp_path / "persona.json"
    p.write_text(json.dumps(persona))

    with pytest.raises(PersonaError) as e:
        load_persona(str(p))
    assert e.value.code == "persona_missing_name"


def test_preconditions_enforced(monkeypatch, tmp_path):
    # Simulate sync missing -> SyncError propagated
    from shieldcraft.services.sync import SyncError

    def raise_sync(root):
        raise SyncError("sync_missing", "no sync")

    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", raise_sync)
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)

    p = tmp_path / "persona.json"
    p.write_text(json.dumps({"name": "Fiona"}))

    with pytest.raises(SyncError):
        load_persona(str(p))

    # Simulate dirty worktree -> PersonaError
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True})
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: False)

    from shieldcraft.persona import WORKTREE_DIRTY
    with pytest.raises(PersonaError) as e:
        load_persona(str(p))
    assert e.value.code == WORKTREE_DIRTY or e.value.code == "worktree_dirty"
