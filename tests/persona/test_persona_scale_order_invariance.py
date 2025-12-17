from shieldcraft.engine import Engine
from shieldcraft.persona import Persona
from shieldcraft.persona.persona_registry import register_persona, clear_registry


def build_with_personas(personas, order_seed=None):
    clear_registry()
    for p in personas:
        register_persona(p)
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True
    engine.checklist_context = type("_", (), {"_events": [], "record_event": lambda *a, **k: None})()
    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}
    return engine.checklist_gen.build(spec, dry_run=True, engine=engine)


def test_multiple_personas_order_irrelevant(monkeypatch):
    # Create personas that only annotate (no authority)
    p1 = Persona(name="p1", scope=["checklist"], allowed_actions=["annotate"], constraints={"constraint": [{"match": {"ptr": "/sections"}, "set": {"meta": {"note": "p1"}}}]})
    p2 = Persona(name="p2", scope=["checklist"], allowed_actions=["annotate"], constraints={"constraint": [{"match": {"ptr": "/sections"}, "set": {"meta": {"note": "p2"}}}]})

    res1 = build_with_personas([p1, p2])
    res2 = build_with_personas([p2, p1])
    # Primary items should be identical ignoring persona-added meta
    def strip_persona_meta(chk):
        out = []
        for it in chk.get("items", []):
            it2 = dict(it)
            meta = dict(it2.get("meta", {}))
            meta.pop("persona_constraints_applied", None)
            meta.pop("persona_constraints_disallowed", None)
            it2["meta"] = meta
            out.append(it2)
        return out

    assert strip_persona_meta(res1) == strip_persona_meta(res2)
