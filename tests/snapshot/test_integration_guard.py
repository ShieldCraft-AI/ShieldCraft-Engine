import json
import os
from shieldcraft.engine import Engine


def test_snapshot_runs_before_execute(monkeypatch, tmp_path):
    # Enable snapshot enforcement
    monkeypatch.setenv("SHIELDCRAFT_SNAPSHOT_ENABLED", "1")

    # Prepare repo with a snapshot that will fail validation
    repo = tmp_path
    # Write snapshot that expects empty tree
    os.makedirs(tmp_path / "artifacts", exist_ok=True)
    with open(tmp_path / "artifacts" / "repo_snapshot.json", "w") as f:
        json.dump({"version": "v1", "files": [], "tree_hash": "deadbeef"}, f)

    monkeypatch.chdir(repo)
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True})
    from shieldcraft.snapshot import SnapshotError

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Use canonical sample spec to get past schema
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    data = json.loads((repo_root / "spec" / "se_dsl_v1.spec.json").read_text())
    data["metadata"]["spec_format"] = "canonical_json_v1"
    spec_path = tmp_path / "s.json"
    spec_path.write_text(json.dumps(data))

    # Execution should raise SnapshotError before plan dir creation
    try:
        engine.execute(str(spec_path))
        assert False, "Expected SnapshotError"
    except SnapshotError:
        pass
