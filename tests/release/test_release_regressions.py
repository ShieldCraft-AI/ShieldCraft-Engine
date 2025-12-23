import json
import os


def test_artifact_contract_summary_behavior(tmp_path, monkeypatch):
    repo = tmp_path
    monkeypatch.chdir(repo)
    os.makedirs(repo / "artifacts", exist_ok=True)
    (repo / "artifacts" / "repo_sync_state.json").write_text(json.dumps({}))
    h = __import__('hashlib').sha256((repo / "artifacts" / "repo_sync_state.json").read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    # Run structured demo (should be STRUCTURED and have conditional artifacts, no guaranteed)
    from shieldcraft.main import run_self_host
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec_path = str(repo_root / "demos" / "structured.json")
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    s = json.loads(open('.selfhost_outputs/summary.json', encoding='utf-8').read())
    assert s.get('conversion_state') in ('STRUCTURED', 'VALID', 'CONVERTIBLE')
    ac = s.get('artifact_contract_summary') or {}
    assert ac.get('guaranteed', []) == [], 'Non-READY specs must not list guaranteed artifacts'


def test_governance_bundle_structure(tmp_path, monkeypatch):
    repo = tmp_path
    monkeypatch.chdir(repo)
    os.makedirs(repo / "artifacts", exist_ok=True)
    (repo / "artifacts" / "repo_sync_state.json").write_text(json.dumps({}))
    h = __import__('hashlib').sha256((repo / "artifacts" / "repo_sync_state.json").read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    from shieldcraft.main import run_self_host
    import pathlib
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec_path = str(repo_root / "demos" / "valid.json")
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    b = json.loads(open('.selfhost_outputs/governance_bundle.json', encoding='utf-8').read())
    for key in ("spec_fingerprint", "conversion_state", "artifact_contract_summary", "progress_summary"):
        assert key in b, f"Governance bundle must include {key}"
