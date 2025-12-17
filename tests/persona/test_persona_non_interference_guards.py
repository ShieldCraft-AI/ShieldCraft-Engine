from shieldcraft.engine import Engine
from shieldcraft.persona import Persona
from shieldcraft.persona.persona_registry import register_persona, clear_registry


def test_personas_cannot_add_or_remove_items(monkeypatch):
    clear_registry()
    # Persona attempts to set a forbidden identifier field
    p = Persona(name="mutant", scope=["checklist"], allowed_actions=["annotate", "veto"], constraints={
        "constraint": [{"match": {"ptr": "/sections"}, "set": {"id": "injected-id"}}]
    })
    register_persona(p)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True
    engine.checklist_context = type("_", (), {"_events": [], "record_event": lambda *a, **k: None})()

    chk = engine.checklist_gen.build({"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}, dry_run=True, engine=engine)
    # Ensure no item with injected id exists and attempt is disallowed
    items = chk.get("items", [])
    assert not any(it.get("id") == "injected-id" for it in items)
    assert any(it.get("meta", {}).get("persona_constraints_disallowed") for it in items)


def test_personas_cannot_modify_refusal_or_outcome_flags(monkeypatch):
    clear_registry()
    p = Persona(name="nagger", scope=["checklist"], allowed_actions=["annotate"], constraints={
        "constraint": [{"match": {"ptr": "/sections"}, "set": {"refusal": True}}]
    })
    register_persona(p)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True
    engine.checklist_context = type("_", (), {"_events": [], "record_event": lambda *a, **k: None})()

    chk = engine.checklist_gen.build({"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}, dry_run=True, engine=engine)
    assert any(it.get("meta", {}).get("persona_constraints_disallowed") for it in chk.get("items", []))
