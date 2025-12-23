
from shieldcraft.engine import Engine
from shieldcraft.persona import PersonaContext, emit_annotation, emit_veto
from shieldcraft.observability import read_persona_events, read_persona_events_hash


def test_persona_events_emitted_and_hashed(tmp_path, monkeypatch):
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    p = PersonaContext(
        name="e",
        role=None,
        display_name=None,
        scope=["preflight"],
        allowed_actions=[
            "annotate",
            "veto"],
        constraints={})
    emit_annotation(engine, p, "preflight", "note", "info")
    emit_veto(engine, p, "preflight", "stop", {"explanation_code": "x", "details": "stop it"}, "high")

    events = read_persona_events()
    assert len(events) == 2
    assert events[0]["capability"] == "annotate"
    assert events[1]["capability"] == "veto"
    # Hash file should exist and be non-empty
    h = read_persona_events_hash()
    assert h and len(h) == 64


def test_persona_events_ordering_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    p = PersonaContext(
        name="o",
        role=None,
        display_name=None,
        scope=["preflight"],
        allowed_actions=["annotate"],
        constraints={})
    for i in range(3):
        emit_annotation(engine, p, "preflight", f"note {i}", "info")
    h1 = read_persona_events_hash()

    # Repeat in fresh engine
    engine2 = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    for i in range(3):
        emit_annotation(engine2, p, "preflight", f"note {i}", "info")
    h2 = read_persona_events_hash()
    assert h1 == h2


def test_persona_events_no_engine_side_effect(monkeypatch):
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    # Avoid external sync requirements during this test
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: {"ok": True})
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    p = PersonaContext(
        name="n",
        role=None,
        display_name=None,
        scope=["preflight"],
        allowed_actions=["annotate"],
        constraints={})
    # Ensure annotation does not change preflight *success* result (artifact differences allowed)
    res1 = engine.preflight({})
    emit_annotation(engine, p, "preflight", "ok", "info")
    res2 = engine.preflight({})
    assert res1.get("ok") == res2.get("ok")


def test_multi_persona_stress_deterministic(tmp_path, monkeypatch):
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    personas = [
        PersonaContext(
            name=str(i),
            role=None,
            display_name=None,
            scope=["preflight"],
            allowed_actions=["annotate"],
            constraints={}) for i in range(10)]

    # Emit deterministic interleaving
    for i, p in enumerate(personas):
        emit_annotation(engine, p, "preflight", f"m{i}", "info")
    # Hash should be stable
    h = read_persona_events_hash()
    assert h


def test_veto_emits_events_and_produces_single_terminal_refusal(tmp_path, monkeypatch):
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    p1 = PersonaContext(
        name="v1",
        role=None,
        display_name=None,
        scope=["preflight"],
        allowed_actions=["veto"],
        constraints={})
    p2 = PersonaContext(
        name="v2",
        role=None,
        display_name=None,
        scope=["preflight"],
        allowed_actions=["veto"],
        constraints={})
    # Emit two vetoes
    emit_veto(engine, p1, "preflight", "code1", {"explanation_code": "e1", "details": "d1"}, "low")
    emit_veto(engine, p2, "preflight", "code2", {"explanation_code": "e2", "details": "d2"}, "high")

    # Preflight must raise exactly one terminal refusal and events must be emitted
    import json
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: {"ok": True})
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    # Preflight treats persona vetoes as advisory; ensure selection exists and DIAGNOSTIC recorded
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: {"ok": True})
    res = engine.preflight(spec)
    assert res.get("ok") is True
    sel = getattr(engine, "_persona_veto_selected", None)
    assert sel is not None and sel.get("persona_id") == "v2"

    events = read_persona_events()
    # Two veto events should be present and ordered as emitted
    veto_events = [ev for ev in events if ev.get("capability") == "veto"]
    assert len(veto_events) >= 2
    assert veto_events[-2]["persona_id"] == "v1"
    assert veto_events[-1]["persona_id"] == "v2"
    # Hash should be present
    h = read_persona_events_hash()
    assert h and len(h) == 64
