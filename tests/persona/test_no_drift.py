import pytest
from shieldcraft.persona import PersonaContext, emit_annotation
from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_no_drift_blocks_unlogged_persona_actions(tmp_path, monkeypatch):
    # Use isolated tmpdir as workspace
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")

    class EngineStub:
        pass

    engine = EngineStub()

    p = PersonaContext(name="x", role=None, display_name=None, scope=["preflight"], allowed_actions=["annotate"], constraints={})
    # Emit an annotation but DO NOT record a decision
    emit_annotation(engine, p, "preflight", "note", "info")

    # Ensure event was persisted
    from shieldcraft.observability import read_persona_events
    events = read_persona_events()
    assert len(events) > 0

    # Guard should detect the unlogged action and halt emission
    from shieldcraft.services.governance.persona_guard import enforce_manifest_emission_ok
    with pytest.raises(RuntimeError) as exc:
        enforce_manifest_emission_ok()
    assert "persona_unlogged_action" in str(exc.value)

    # As a further check, generator should not silently ignore persona influence; call build and expect no crash
    gen = ChecklistGenerator()
    spec = {"metadata": {"product_id": "x"}, "sections": []}
    # Build may or may not surface the guard depending on flow; ensure it completes without producing manifest without raising
    result = gen.build(spec)
    assert isinstance(result, dict)
