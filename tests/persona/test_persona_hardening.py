import json
import os

import pytest

from shieldcraft.engine import Engine
from shieldcraft.persona import (
    Persona,
    PersonaContext,
    load_persona,
    find_persona_files,
    resolve_persona_files,
    detect_conflicts,
    emit_annotation,
    emit_veto,
    PersonaError,
    PERSONA_CONFLICT_DUPLICATE_NAME,
    PERSONA_MISSING_VERSION,
    PERSONA_RATE_LIMIT_EXCEEDED,
    PERSONA_INVALID_VETO_EXPLANATION,
)


def _write_persona_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def test_duplicate_persona_files_detected(tmp_path, monkeypatch):
    repo = tmp_path
    p1 = repo / "personas" / "a.json"
    p2 = repo / "personas" / "a-dup.json"
    _write_persona_file(str(p1), {"name": "a", "persona_version": "v1", "version": "1.0"})
    _write_persona_file(str(p2), {"name": "a", "persona_version": "v1", "version": "1.1"})
    files = [str(p1), str(p2)]
    errors = detect_conflicts(files)
    assert any(e["code"] == PERSONA_CONFLICT_DUPLICATE_NAME for e in errors)


def test_missing_version_fails(tmp_path, monkeypatch):
    # Create persona file missing 'version'
    p = tmp_path / "persona.json"
    _write_persona_file(str(p), {"name": "nover", "persona_version": "v1"})
    # Ensure preconditions pass so we hit validation
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True})
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)
    with pytest.raises(PersonaError) as e:
        load_persona(str(p))
    assert e.value.code == PERSONA_MISSING_VERSION


def test_annotation_rate_limit_enforced(tmp_path, monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    persona = PersonaContext(name="rate", role=None, display_name=None, scope=["preflight"], allowed_actions=["annotate"], constraints={})
    for i in range(5):
        emit_annotation(engine, persona, "preflight", f"note {i}", "info")
    with pytest.raises(PersonaError) as e:
        emit_annotation(engine, persona, "preflight", "overflow", "info")
    assert e.value.code == PERSONA_RATE_LIMIT_EXCEEDED


def test_veto_explanation_schema_enforced(tmp_path, monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    persona = PersonaContext(name="v1", role=None, display_name=None, scope=["preflight"], allowed_actions=["veto"], constraints={})
    # explanation must be dict with explanation_code and details
    with pytest.raises(PersonaError) as e:
        emit_veto(engine, persona, "preflight", "bad", "not a dict", "high")
    assert e.value.code == PERSONA_INVALID_VETO_EXPLANATION


def test_persona_determinism_assertions(tmp_path, monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    p = PersonaContext(name="d", role=None, display_name=None, scope=["preflight"], allowed_actions=["annotate", "veto"], constraints={})
    emit_annotation(engine, p, "preflight", "a1", "info")
    emit_veto(engine, p, "preflight", "stop", {"explanation_code": "x", "details": "stop it"}, "high")
    # Run preflight (will raise persona_veto)
    try:
        engine.preflight({})
    except RuntimeError:
        pass
    first = open(os.path.join("artifacts", "persona_annotations_v1.json")).read()

    # Reset and repeat
    engine2 = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    emit_annotation(engine2, p, "preflight", "a1", "info")
    emit_veto(engine2, p, "preflight", "stop", {"explanation_code": "x", "details": "stop it"}, "high")
    try:
        engine2.preflight({})
    except RuntimeError:
        pass
    second = open(os.path.join("artifacts", "persona_annotations_v1.json")).read()
    assert first == second


def test_cross_persona_interference(tmp_path, monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    p1 = PersonaContext(name="one", role=None, display_name=None, scope=["preflight"], allowed_actions=["annotate"], constraints={})
    p2 = PersonaContext(name="two", role=None, display_name=None, scope=["preflight"], allowed_actions=["annotate"], constraints={})
    emit_annotation(engine, p1, "preflight", "from one", "info")
    emit_annotation(engine, p2, "preflight", "from two", "info")
    anns = json.load(open(os.path.join("artifacts", "persona_annotations_v1.json")))
    assert any(a["persona_id"] == "one" and a["message"] == "from one" for a in anns)
    assert any(a["persona_id"] == "two" and a["message"] == "from two" for a in anns)
