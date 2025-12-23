from shieldcraft.persona.persona_registry import register_persona, clear_registry
from shieldcraft.persona import Persona
from shieldcraft.engine import Engine


def test_persona_cannot_create_artifacts(monkeypatch):
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    clear_registry()

    # Persona attempts to set forbidden field 'id' via a constraint
    p = Persona(name="malicious", scope=["checklist"], allowed_actions=["annotate"], constraints={
        "constraint": [{"match": {"ptr": "/metadata"}, "set": {"id": "injected"}}]
    })
    register_persona(p)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True

    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}

    # Persona creation attempts are disallowed and recorded but should not raise
    res = engine.checklist_gen.build(spec, engine=engine)
    assert isinstance(res, dict)
    items = res.get("items", [])
    assert any(it.get("meta", {}).get("persona_constraints_disallowed") for it in items)
