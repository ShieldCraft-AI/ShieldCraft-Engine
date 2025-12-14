import json
import os
import shutil
import tempfile
import pathlib

from shieldcraft.main import run_self_host


def test_run_selfhost_writes_snapshot_errors(monkeypatch, tmp_path):
    # Ensure snapshot enforcement is enabled
    monkeypatch.setenv("SHIELDCRAFT_SNAPSHOT_ENABLED", "1")

    # Prepare repo with a snapshot that will fail validation
    repo = tmp_path
    os.makedirs(tmp_path / "artifacts", exist_ok=True)
    with open(tmp_path / "artifacts" / "repo_snapshot.json", "w") as f:
        json.dump({"version": "v1", "hash_algorithm": "sha256", "files": [], "tree_hash": "deadbeef"}, f)

    # Prepare a minimal self-host spec file
    spec = {
        "metadata": {"product_id": "test-snap", "version": "1.0", "spec_format": "canonical_json_v1", "self_host": True},
        "model": {"version": "1.0"},
        "sections": {}
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))

    # chdir to repo and run self-host; ensure sync check passes so snapshot validation runs
    cwd = os.getcwd()
    try:
        os.chdir(repo)
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        # ensure repo sync is reported OK
        monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True, "artifact": "artifacts/repo_sync_state.json", "sha256": "abc"})
        run_self_host(str(spec_path), "src/shieldcraft/dsl/schema/se_dsl.schema.json")
        err = os.path.join('.selfhost_outputs', 'errors.json')
        assert os.path.exists(err)
        data = json.load(open(err))
        assert 'errors' in data
        assert data['errors'][0]['code'] in ('snapshot_mismatch', 'snapshot_invalid')
    finally:
        os.chdir(cwd)
