import os
from shieldcraft.observability import read_persona_events, read_persona_events_hash


def test_persona_event_and_hash_emitted_together(tmp_path, monkeypatch):
    # Ensure persona system emits both event file and hash together
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    from shieldcraft.engine import Engine
    from shieldcraft.persona import PersonaContext, emit_annotation
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    p = PersonaContext(name="c", role=None, display_name=None, scope=["preflight"], allowed_actions=["annotate"], constraints={})
    # Remove any pre-existing artifacts
    for f in ("artifacts/persona_events_v1.json", "artifacts/persona_events_v1.hash"):
        try:
            os.remove(f)
        except Exception:
            pass

    emit_annotation(engine, p, "preflight", "note", "info")
    events = read_persona_events()
    h = read_persona_events_hash()
    assert bool(events) is True
    assert h and len(h) == 64