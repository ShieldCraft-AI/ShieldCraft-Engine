from shieldcraft.persona.runtime import PersonaRuntime
from shieldcraft.persona import PersonaContext
from shieldcraft.observability import read_persona_events


def test_persona_decisions_are_recorded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    class EngineStub:
        pass

    engine = EngineStub()
    p = PersonaContext(
        name="auditor",
        role=None,
        display_name=None,
        scope=["preflight"],
        allowed_actions=["annotate"],
        constraints={})
    rt = PersonaRuntime(engine)

    dec = rt.evaluate(p, "annotate", "preflight", {"message": "ok", "severity": "info"})
    # decision should be recorded; read events
    events = read_persona_events()
    # Find a decision event
    assert any(e.get("capability") == "decision" for e in events)
    # Runtime list should be present
    assert hasattr(engine, "_persona_decisions")
    assert engine._persona_decisions[0]["decision"] == dec
