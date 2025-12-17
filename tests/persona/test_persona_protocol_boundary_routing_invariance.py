import json
from shieldcraft.engine import Engine
from shieldcraft.persona import Persona, PersonaContext
from shieldcraft.persona.persona_registry import register_persona, clear_registry


def make_stub_context():
    class StubCtx:
        def __init__(self):
            self._events = []
        def record_event(self, code, phase, severity, message=None, evidence=None):
            self._events.append({"code": code, "phase": phase, "severity": severity, "message": message, "evidence": evidence})
        def get_events(self):
            return self._events
    return StubCtx()


def test_persona_routing_invariance(monkeypatch, tmp_path):
    # Deterministic spec fixture
    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}

    # Baseline: personas disabled
    engine_no = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine_no.checklist_context = make_stub_context()
    engine_no.persona_enabled = False
    chk_no = engine_no.checklist_gen.build(spec, dry_run=True, engine=engine_no)

    # Enable personas and register a persona that emits advisory constraints and a veto
    clear_registry()
    p = Persona(name="adv", scope=["checklist"], allowed_actions=["annotate", "veto"], constraints={
        "constraint": [{"match": {"ptr": "/sections"}, "set": {"meta": {"advisor_note": "review"}}}],
        # Use an all-match veto so it is recorded deterministically for the test
        "veto": [{"match": {}, "code": "no-sections", "explanation": {"explanation_code": "no-sections", "details": "sections flagged"}, "severity": "low"}]
    })
    register_persona(p)

    engine_yes = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine_yes.checklist_context = make_stub_context()
    engine_yes.persona_enabled = True
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")

    chk_yes = engine_yes.checklist_gen.build(spec, dry_run=True, engine=engine_yes)

    # The primary checklist items and outcomes must be identical
    def strip_persona_meta(chk):
        out = []
        for it in chk.get("items", chk.get("items", [])):
            it2 = dict(it)
            meta = dict(it2.get("meta", {}))
            # remove persona-added metadata
            meta.pop("persona_constraints_applied", None)
            meta.pop("persona_constraints_disallowed", None)
            it2["meta"] = meta
            out.append(it2)
        return out

    assert strip_persona_meta(chk_no) == strip_persona_meta(chk_yes)
    # Persona routing recorded only as advisory events/metadata
    evs = engine_yes.checklist_context.get_events()
    assert any(e.get("code") == "G7_PERSONA_VETO" for e in evs) or getattr(engine_yes, "_persona_veto_selected", None)


