import json

from shieldcraft.engine import Engine


def test_rejects_unlisted_artifact_in_preview(monkeypatch, tmp_path):
    # Ensure worktree is considered clean
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open('spec/se_dsl_v1.spec.json'))
    preview = engine.run_self_host(spec, dry_run=True)
    # Simulate a malicious output path not in allowed prefixes
    malicious = "../secrets/passwords.txt"
    # The engine should not claim or allow such an output in preview
    assert all(not out.get('path', '').startswith('..') for out in preview.get('outputs', []))
