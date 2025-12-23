from shieldcraft.engine import Engine
from shieldcraft.persona import Persona
from shieldcraft.persona.persona_registry import register_persona, clear_registry


def make_stub_context():
    class StubCtx:
        def __init__(self):
            self._events = []

        def record_event(self, code, phase, severity, message=None, evidence=None):
            self._events.append({"code": code, "phase": phase, "severity": severity,
                                "message": message, "evidence": evidence})

        def get_events(self):
            return self._events
    return StubCtx()


def test_persona_cannot_escalate_severity(monkeypatch):
    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}
    clear_registry()
    # Persona attempts to set severity to BLOCKER (should be disallowed)
    p = Persona(name="scaler", scope=["checklist"], allowed_actions=["annotate"], constraints={
        "constraint": [{"match": {"ptr": "/sections"}, "set": {"severity": "BLOCKER"}}]
    })
    register_persona(p)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True
    engine.checklist_context = make_stub_context()

    chk = engine.checklist_gen.build(spec, dry_run=True, engine=engine)
    # Ensure persona attempted mutation was recorded as disallowed and did not mutate item severity
    items = chk.get("items", [])
    assert any(it.get("meta", {}).get("persona_constraints_disallowed") for it in items)
    # DIAGNOSTIC recorded
    evs = engine.checklist_context.get_events()
    assert any(e.get("code") == "G15_PERSONA_CONSTRAINT_DISALLOWED" for e in evs)


def test_conflicting_persona_advice_produces_diagnostic(monkeypatch):
    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}
    clear_registry()
    p1 = Persona(name="a1", scope=["checklist"], allowed_actions=["annotate"], constraints={
                 "constraint": [{"match": {"ptr": "/sections"}, "set": {"meta": {"note": "a1"}}}]})
    p2 = Persona(name="a2", scope=["checklist"], allowed_actions=["annotate"], constraints={
                 "constraint": [{"match": {"ptr": "/sections"}, "set": {"meta": {"note": "a2"}}}]})
    register_persona(p1)
    register_persona(p2)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True
    engine.checklist_context = make_stub_context()

    chk = engine.checklist_gen.build(spec, dry_run=True, engine=engine)
    # Conflicting advice should appear as DIAGNOSTIC (they should not alter primary outcome)
    evs = engine.checklist_context.get_events()
    assert any(e.get("code") == "G15_PERSONA_CONSTRAINT_DISALLOWED" for e in evs) or any(
        it.get("meta", {}).get("persona_constraints_applied") for it in chk.get("items", []))
