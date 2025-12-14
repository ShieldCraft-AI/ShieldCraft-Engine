import json
import os
import shutil

from shieldcraft.engine import Engine
from shieldcraft.persona import Persona, PersonaContext, emit_annotation, emit_veto


def test_persona_annotation_does_not_affect_outputs(tmp_path, monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    # Enable persona feature for test
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    # Prepare persona context with scope for preflight
    persona = PersonaContext(name="fiona", role="reviewer", display_name="Fiona", scope=["preflight"], allowed_actions=["annotate"], constraints={})
    # Emit annotation
    emit_annotation(engine, persona, "preflight", "Looks good", "low")

    # Preflight should proceed normally and outputs should be unaffected
    pre = engine.preflight(spec)
    assert pre.get("ok") is True
    # Annotations artifact should exist and be deterministic
    annotations = json.load(open(os.path.join("artifacts", "persona_annotations_v1.json")))
    assert annotations[-1]["persona_id"] == "fiona"


def test_persona_veto_halts_execution_cleanly(tmp_path, monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    persona = PersonaContext(name="fiona", role="reviewer", display_name="Fiona", scope=["preflight"], allowed_actions=["veto"], constraints={})
    # Emit veto with structured explanation
    emit_veto(engine, persona, "preflight", "forbidden", {"explanation_code": "forbidden_reason", "details": "vetoed by persona"}, "high")

    try:
        engine.preflight(spec)
        assert False, "Expected persona_veto RuntimeError"
    except RuntimeError as e:
        assert "persona_veto" in str(e)


def test_multi_persona_resolution(tmp_path, monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    p1 = PersonaContext(name="a", role=None, display_name=None, scope=["preflight"], allowed_actions=["veto"], constraints={})
    p2 = PersonaContext(name="b", role=None, display_name=None, scope=["preflight"], allowed_actions=["veto"], constraints={})
    emit_veto(engine, p1, "preflight", "lowcode", {"explanation_code": "low", "details": "low severity"}, "low")
    emit_veto(engine, p2, "preflight", "highcode", {"explanation_code": "high", "details": "high severity"}, "high")
    try:
        engine.preflight(spec)
        assert False, "Expected persona_veto"
    except RuntimeError as e:
        # Should pick the high severity veto from persona b
        assert "b:highcode" in str(e)
