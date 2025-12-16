import pytest
from shieldcraft.persona import PersonaContext, emit_veto


def test_veto_blocks_preflight(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")

    class EngineStub:
        pass

    engine = EngineStub()
    p = PersonaContext(name="v", role=None, display_name=None, scope=["preflight"], allowed_actions=["veto"], constraints={})
    # emit_veto does not raise immediately; it records a veto in engine state and emits an event
    emit_veto(engine, p, "preflight", "stop", {"explanation_code": "e1", "details": "stop"}, "high")
    # Ensure veto recorded on engine and events persisted
    assert hasattr(engine, "_persona_vetoes")
    from shieldcraft.observability import read_persona_events
    events = read_persona_events()
    assert any(e.get("capability") == "veto" for e in events)
