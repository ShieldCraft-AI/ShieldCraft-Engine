import os
import json

import pytest

from shieldcraft.persona import (
    PERSONA_ENTRY_POINTS,
    PERSONA_STABLE,
    PERSONA_COMPLETE,
    PERSONA_VERSION_INCOMPATIBLE,
    load_persona,
)


def test_persona_entry_points_registered():
    # We expect exactly two entry points: annotate and veto
    caps = {c for c, n in PERSONA_ENTRY_POINTS}
    assert caps == {"annotate", "veto"}


def test_persona_stability_markers_present():
    assert PERSONA_STABLE is True
    assert PERSONA_COMPLETE is True


def test_reject_future_persona_version(tmp_path, monkeypatch):
    p = tmp_path / "persona.json"
    p.write_text(json.dumps({"persona_version": "v2", "name": "F", "version": "1.0"}))
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True})
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)
    with pytest.raises(Exception) as e:
        load_persona(str(p))
    # Ensure the specific incompatibility code is used
    assert getattr(e.value, "code", None) == PERSONA_VERSION_INCOMPATIBLE


def test_disabling_persona_removes_artifacts(tmp_path, monkeypatch):
    # Ensure no persona artifacts are created when feature disabled
    monkeypatch.delenv("SHIELDCRAFT_PERSONA_ENABLED", raising=False)
    # Simulate a run which would otherwise create artifacts through normal execution
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Ensure no pre-existing persona artifacts
    for f in (os.path.join("artifacts", "persona_events_v1.json"), os.path.join("artifacts", "persona_events_v1.hash")):
        try:
            os.remove(f)
        except Exception: # type: ignore
            pass
    # No exception: persona disabled means emission APIs are not called
    res = engine.preflight({})
    # Artifacts should not exist after the run
    assert not os.path.exists(os.path.join("artifacts", "persona_events_v1.json"))
    assert not os.path.exists(os.path.join("artifacts", "persona_events_v1.hash"))
