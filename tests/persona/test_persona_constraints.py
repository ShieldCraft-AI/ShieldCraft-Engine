from shieldcraft.persona.persona_registry import register_persona, clear_registry
from shieldcraft.persona import Persona
from shieldcraft.engine import Engine


def test_persona_constraints_shape_checklist(monkeypatch):
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    clear_registry()

    p = Persona(name="constrainer", scope=["checklist"], allowed_actions=["annotate"], constraints={
        # target an existing pointer that is present in generated items
        "constraint": [{"match": {"ptr": "/metadata"}, "set": {"severity": "low"}}]
    })
    register_persona(p)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True

    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}

    res = engine.checklist_gen.build(spec, engine=engine)
    items = res["items"]
    # Persona attempt to change severity should be disallowed and recorded
    md = [i for i in items if i.get("ptr") == "/metadata"]
    assert md
    assert any(it.get("meta", {}).get("persona_constraints_disallowed") for it in items)
    # Ensure original severity retained (default behavior)
    assert md[0].get("severity") != "low"
