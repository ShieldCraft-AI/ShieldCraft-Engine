import json
import tempfile
import os
import pathlib


def test_sync_gate_invoked_for_all_modes(monkeypatch, tmp_path):
    from shieldcraft.engine import Engine
    from shieldcraft.services.sync import REPO_STATE_FILENAME, REPO_SYNC_ARTIFACT

    calls = []

    def spy(root):
        calls.append(root)
        # emulate normal response
        return {"ok": True, "artifact": REPO_SYNC_ARTIFACT, "sha256": "abc"}

    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", spy)

    # run in external mode to ensure verify_repo_sync is invoked (external is opt-in)
    monkeypatch.setenv("SHIELDCRAFT_SYNC_AUTHORITY", "external")
    monkeypatch.setenv("SHIELDCRAFT_ALLOW_EXTERNAL_SYNC", "1")

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Prepare a valid canonical spec file
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    data = json.loads((repo_root / "spec" / "se_dsl_v1.spec.json").read_text())
    data["metadata"]["spec_format"] = "canonical_json_v1"
    spec_path = tmp_path / "s.json"
    spec_path.write_text(json.dumps(data))

    # Call multiple entrypoints
    engine.preflight(str(spec_path))
    try:
        engine.execute(str(spec_path))
    except Exception:
        # may raise for other reasons but sync should have been invoked
        pass
    try:
        engine.run_self_host(data, dry_run=True)
    except Exception:
        pass

    # Expect spy to have been called at least once per attempted invocation
    assert len(calls) >= 3
