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


def test_engine_accepts_normalized_ingestion_envelope(monkeypatch):
    """Ensure the deterministic ingestion envelope (metadata+raw_input) is accepted."""
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Ensure repo sync and worktree checks pass so we reach the self-host input gate
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: {"ok": True, "sha256": "abc"})
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)

    envelope = {"metadata": {"normalized": True, "source_format": "yaml"}, "raw_input": "some text"}
    # The envelope should be accepted; dry_run returns a preview dict
    res = engine.run_self_host(envelope, dry_run=True)
    assert isinstance(res, dict)
    assert "manifest" in res


def test_engine_refuses_on_persona_veto(monkeypatch):
    from shieldcraft.engine import Engine
    from shieldcraft.persona import PersonaContext, emit_veto
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    # Emit veto and ensure preflight raises persona_veto
    p = PersonaContext(name="x", role=None, display_name=None, scope=["preflight"], allowed_actions=["veto"], constraints={})
    emit_veto(engine, p, "preflight", "forbid", {"explanation_code": "reason", "details": "stop"}, "high")
    with pytest.raises(RuntimeError) as e:
        engine.preflight(spec)
    assert "persona_veto" in str(e.value)
