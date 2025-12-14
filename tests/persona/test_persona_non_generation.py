import pytest
from shieldcraft.persona.persona_registry import register_persona, clear_registry
from shieldcraft.persona import Persona
from shieldcraft.engine import Engine


def test_persona_cannot_create_artifacts(monkeypatch):
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    clear_registry()

    # Persona attempts to set forbidden field 'id' via a constraint
    p = Persona(name="malicious", scope=["checklist"], allowed_actions=["annotate"], constraints={
        "constraint": [{"match": {"ptr": "/"}, "set": {"id": "injected"}}]
    })
    register_persona(p)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True

    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}

    with pytest.raises(RuntimeError) as exc:
        engine.checklist_gen.build(spec, engine=engine)
    assert "persona_side_effects_disallowed" in str(exc.value) or "persona_side_effects_disallowed" == str(exc.value)
