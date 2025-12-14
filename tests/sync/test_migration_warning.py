import os
import logging
from shieldcraft.services.sync import verify_repo_state_authoritative


def test_migration_warning_logged(tmp_path, caplog, monkeypatch):
    caplog.set_level(logging.WARNING, logger="shieldcraft.snapshot")
    # create minimal repo_state to satisfy external check
    os.makedirs(tmp_path / "artifacts", exist_ok=True)
    with open(tmp_path / "artifacts" / "repo_sync_state.json", "w") as f:
        f.write("x")
    # compute sha and write repo_state_sync.json
    import hashlib, json
    h = hashlib.sha256(open(tmp_path / "artifacts" / "repo_sync_state.json", "rb").read()).hexdigest()
    with open(tmp_path / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    # invoke external authority explicitly (external is now opt-in)
    monkeypatch.setenv("SHIELDCRAFT_SYNC_AUTHORITY", "external")
    monkeypatch.setenv("SHIELDCRAFT_ALLOW_EXTERNAL_SYNC", "1")
    monkeypatch.chdir(tmp_path)
    verify_repo_state_authoritative(str(tmp_path))
    assert any("snapshot_deprecation" in r.message for r in caplog.records)
