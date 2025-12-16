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

    with pytest.raises(RuntimeError) as exc:
        engine.checklist_gen.build(spec, engine=engine)
    assert "persona_veto" in str(exc.value)
