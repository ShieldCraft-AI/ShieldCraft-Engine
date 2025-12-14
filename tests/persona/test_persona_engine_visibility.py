import json
import os
import pathlib

from shieldcraft.engine import Engine


def test_engine_exposes_persona_when_enabled(monkeypatch, tmp_path):
    # Enable persona flag
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")

    # Prepare repo with persona files
    repo = tmp_path
    p = repo / "persona.json"
    p.write_text(json.dumps({"name": "Fiona", "persona_version": "v1", "version": "1.0"}))

    monkeypatch.chdir(repo)
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True})
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Persona loading happens during run_self_host (in our scaffold)
    engine.run_self_host(json.load(open(pathlib.Path(__file__).resolve().parents[2] / "spec" / "se_dsl_v1.spec.json")), dry_run=True)

    assert engine.persona is not None
    assert engine.persona.name == "Fiona"
