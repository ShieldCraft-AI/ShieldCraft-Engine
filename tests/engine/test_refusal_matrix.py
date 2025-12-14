import json
import pytest


def test_engine_refuses_on_unclean_worktree(monkeypatch):
    from shieldcraft.engine import Engine
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: False)
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    spec["metadata"]["spec_format"] = "canonical_json_v1"
    with pytest.raises(RuntimeError) as e:
        engine.run_self_host(spec, dry_run=True)
    assert "worktree_not_clean" in str(e.value)


def test_engine_refuses_on_missing_sync(monkeypatch):
    from shieldcraft.engine import Engine
    from shieldcraft.services.sync import SyncError
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    spec["metadata"]["spec_format"] = "canonical_json_v1"
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: (_ for _ in ()).throw(SyncError("sync_missing", "missing sync")))
    with pytest.raises(SyncError):
        engine.run_self_host(spec, dry_run=True)


def test_engine_refuses_on_disallowed_input():
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    bad_spec = {"metadata": {"self_host": True}, "unexpected": 1}
    with pytest.raises(RuntimeError) as e:
        engine.run_self_host(bad_spec, dry_run=True)
    assert "disallowed_selfhost_input" in str(e.value)
