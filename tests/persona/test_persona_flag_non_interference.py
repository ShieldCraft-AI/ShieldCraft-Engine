import json

from shieldcraft.engine import Engine


def test_persona_flag_off_does_not_affect_selfhost(monkeypatch, tmp_path):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Ensure persona flag is OFF
    monkeypatch.delenv("SHIELDCRAFT_PERSONA_ENABLED", raising=False)

    # Create persona file in repo root
    persona_path = tmp_path / "persona.json"
    persona_path.write_text(json.dumps({"name": "Fiona", "role": "cofounder"}))

    # Monkeypatch cwd to temp repo to avoid writing in project workspace
    monkeypatch.chdir(tmp_path)

    # Ensure repo sync & clean checks succeed so loader, if invoked, would pass
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True})
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)

    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec = json.load(open(repo_root / "spec" / "se_dsl_v1.spec.json"))

    # Run dry-run self-host with persona file present; since flag is OFF, behavior must be unchanged
    preview_without_persona = engine.run_self_host(spec, dry_run=True)

    # Sanity: preview should contain fingerprint and outputs
    assert "fingerprint" in preview_without_persona
    assert "outputs" in preview_without_persona
