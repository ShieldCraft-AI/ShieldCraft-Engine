import json
import hashlib
import os


def test_artifact_contract_summary_deterministic(tmp_path, monkeypatch):
    # Prepare repo sync artifact
    repo = tmp_path
    monkeypatch.chdir(repo)
    os.makedirs(repo / "artifacts", exist_ok=True)
    (repo / "artifacts" / "repo_sync_state.json").write_text(json.dumps({}))
    h = hashlib.sha256((repo / "artifacts" / "repo_sync_state.json").read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec = json.load(open(repo_root / "spec" / "se_dsl_v1.spec.json"))
    spec["metadata"]["spec_format"] = "canonical_json_v1"

    p1 = engine.run_self_host(spec, dry_run=True)
    p2 = engine.run_self_host(spec, dry_run=True)

    a1 = p1["manifest"].get("artifact_contract_summary")
    a2 = p2["manifest"].get("artifact_contract_summary")
    assert a1 == a2
