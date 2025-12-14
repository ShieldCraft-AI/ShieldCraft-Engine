import os
import json
import hashlib


def test_allowlist_permits_known_diff(tmp_path, monkeypatch):
    from shieldcraft.engine import Engine
    from pathlib import Path

    repo = tmp_path
    os.makedirs(repo / "artifacts", exist_ok=True)
    (repo / "artifacts" / "repo_sync_state.json").write_text('{}')
    h = hashlib.sha256((repo / "artifacts" / "repo_sync_state.json").read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    monkeypatch.chdir(repo)
    monkeypatch.setenv('SHIELDCRAFT_SELFBUILD_ENABLED', '1')
    monkeypatch.setenv('SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE', '1')

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    res = engine.run_self_build('spec/se_dsl_v1.spec.json', dry_run=False)
    out_dir = res.get('output_dir')

    # Create an allowlist that permits repo_snapshot.json to differ
    baseline_dir = Path('artifacts/self_build/baseline/v1')
    allowlist = {'version': 1, 'allowed_diffs': ['repo_snapshot.json']}
    (baseline_dir / 'baseline_allowlist_v1.json').write_text(json.dumps(allowlist, sort_keys=True))

    # Corrupt emitted snapshot
    snap_path = Path(out_dir) / 'repo_snapshot.json'
    snap = json.loads(snap_path.read_text())
    snap['tree_hash'] = 'cafebabe'
    snap_path.write_text(json.dumps(snap, sort_keys=True))

    # Should pass now because allowlist permits this diff
    monkeypatch.delenv('SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE', raising=False)
    res2 = engine.run_self_build('spec/se_dsl_v1.spec.json', dry_run=False)
    assert res2.get('ok') is True
