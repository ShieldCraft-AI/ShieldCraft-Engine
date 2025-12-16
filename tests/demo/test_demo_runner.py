import json
import hashlib
import os
import shutil


def test_demo_runner_determinism(tmp_path, monkeypatch):
    repo = tmp_path
    monkeypatch.chdir(repo)
    os.makedirs(repo / "artifacts", exist_ok=True)
    (repo / "artifacts" / "repo_sync_state.json").write_text(json.dumps({}))
    h = hashlib.sha256((repo / "artifacts" / "repo_sync_state.json").read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    # Ensure worktree clean
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)

    from scripts.demo.run_demo import run

    # Run twice, clearing persisted state between runs to ensure identical starts
    if os.path.exists('products'):
        shutil.rmtree('products')
    run()
    out1 = sorted(os.listdir('demo_outputs'))
    # Read governance bundles and reports
    b1 = {}
    for d in out1:
        p = os.path.join('demo_outputs', d, 'governance_bundle.json')
        if os.path.exists(p):
            b1[d] = open(p,'rb').read()
    r1 = open('demo_outputs/demo_report.md','rb').read()

    # Clear products to remove persisted previous_state
    if os.path.exists('products'):
        shutil.rmtree('products')
    run()
    out2 = sorted(os.listdir('demo_outputs'))
    b2 = {}
    for d in out2:
        p = os.path.join('demo_outputs', d, 'governance_bundle.json')
        if os.path.exists(p):
            b2[d] = open(p,'rb').read()
    r2 = open('demo_outputs/demo_report.md','rb').read()

    assert out1 == out2
    assert r1 == r2
    assert set(b1.keys()) == set(b2.keys())
    for k in b1:
        assert b1[k] == b2[k]
