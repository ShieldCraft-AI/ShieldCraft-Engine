import json
import hashlib
import os


def test_governance_bundle_deterministic(tmp_path, monkeypatch):
    repo = tmp_path
    monkeypatch.chdir(repo)
    os.makedirs(repo / "artifacts", exist_ok=True)
    (repo / "artifacts" / "repo_sync_state.json").write_text(json.dumps({}))
    h = hashlib.sha256((repo / "artifacts" / "repo_sync_state.json").read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    from shieldcraft.main import run_self_host
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec_path = str(repo_root / "spec" / "se_dsl_v1.spec.json")

    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    b1 = open('.selfhost_outputs/governance_bundle.json', 'rb').read()
    a1 = open('.selfhost_outputs/audit_index.json', 'rb').read()

    # Re-run (remove persisted prior state to keep identical starting conditions)
    import shutil
    if os.path.exists('products'):
        shutil.rmtree('products')
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    b2 = open('.selfhost_outputs/governance_bundle.json', 'rb').read()
    a2 = open('.selfhost_outputs/audit_index.json', 'rb').read()

    assert b1 == b2
    assert a1 == a2

    # Bundle must include required keys and match manifest/summary
    bundle = json.loads(b1)
    assert "spec_fingerprint" in bundle
    assert "conversion_state" in bundle
    assert "artifact_contract_summary" in bundle
