import os
import pytest
from shieldcraft.persona.persona_registry import register_persona, clear_registry
from shieldcraft.persona import Persona
from shieldcraft.engine import Engine


def test_persona_veto_halts_engine(monkeypatch, tmp_path):
    # Enable persona feature flag
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    clear_registry()

    # Register a persona that vetoes any item at the root pointer
    p = Persona(name="voter", scope=["checklist"], allowed_actions=["veto"], constraints={
        # target an existing pointer to ensure a match
        "veto": [{"match": {"ptr": "/sections"}, "code": "no-sections", "explanation": {"explanation_code": "no-sections", "details": "sections not allowed"}}]
    })
    register_persona(p)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True

    # Minimal spec that will produce at least one checklist item
    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}

    # Persona veto is advisory; build proceeds normally and records advisory event
    # attach a simple context to capture events
    class StubCtx:
        def __init__(self):
            self._events = []
        def record_event(self, code, phase, severity, message=None, evidence=None):
            self._events.append({"code": code, "phase": phase, "severity": severity, "message": message, "evidence": evidence})
        def get_events(self):
            return self._events
    engine.checklist_context = StubCtx()
    res = engine.checklist_gen.build(spec, engine=engine)
    assert isinstance(res, dict)
    evs = engine.checklist_context.get_events()
    assert any(e.get("code") == "G7_PERSONA_VETO" for e in evs)
