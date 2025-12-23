import json
import os


def test_run_self_host_writes_sync_errors(tmp_path):
    from shieldcraft.main import run_self_host

    # Create minimal spec file
    spec_path = tmp_path / "spec.json"
    spec = {
        "metadata": {"product_id": "test-sync-cli", "spec_format": "canonical_json_v1", "self_host": True},
        "model": {"version": "1.0"},
        "sections": [],
    }
    spec_path.write_text(json.dumps(spec))

    # Ensure no repo_state_sync.json in current cwd
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        run_self_host(str(spec_path), "src/shieldcraft/dsl/schema/se_dsl.schema.json")

        err = os.path.join(".selfhost_outputs", "errors.json")
        assert os.path.exists(err)
        with open(err) as f:
            data = json.load(f)
        assert isinstance(data.get("errors"), list)
        # Ensure the CLI error uses a sync or snapshot-related error code
        assert data["errors"][0]["code"] in (
            "sync_missing",
            "sync_hash_mismatch",
            "sync_invalid_format",
            "snapshot_missing",
            "snapshot_invalid")
    finally:
        os.chdir(cwd)
