import os
import json
import hashlib


def _prepare_repo_for_tests(tmp_dir):
    os.makedirs(tmp_dir / "artifacts", exist_ok=True)
    (tmp_dir / "artifacts" / "repo_sync_state.json").write_text('{}')
    h = hashlib.sha256((tmp_dir / "artifacts" / "repo_sync_state.json").read_bytes()).hexdigest()
    with open(tmp_dir / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)


def test_selfbuild_roundtrip(tmp_path, monkeypatch):
    from shieldcraft.engine import Engine
    from shieldcraft.services.sync import verify_repo_state_authoritative

    repo = tmp_path
    # Prepare minimal sync artifact and mark worktree clean
    _prepare_repo_for_tests(repo)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)

    monkeypatch.chdir(repo)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    monkeypatch.setenv('SHIELDCRAFT_SELFBUILD_ENABLED', '1')
    monkeypatch.setenv('SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE', '1')
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec = json.load(open(repo_root / "spec" / "se_dsl_v1.spec.json"))
    spec["metadata"]["spec_format"] = "canonical_json_v1"

    res = engine.run_self_build("spec/se_dsl_v1.spec.json", dry_run=False)
    assert res.get("ok") is True
    out_dir = res.get("output_dir")
    # First baseline established; now remove the establish flag
    monkeypatch.delenv('SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE', raising=False)
    # Re-ingest produced repo_snapshot.json as external artifact and verify parity
    artifact_path = repo / "artifacts" / "repo_sync_state.json"
    emitted_snap = json.load(open(os.path.join(out_dir, "repo_snapshot.json")))
    artifact_path.write_text(json.dumps(emitted_snap, sort_keys=True))
    h = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    # Should not raise
    _ = verify_repo_state_authoritative(str(repo))


def test_selfbuild_recursion_guard(tmp_path):
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Simulate recursion
    engine._selfbuild_running = True
    try:
        try:
            engine.run_self_build("spec/se_dsl_v1.spec.json", dry_run=True)
            assert False, "Expected recursion guard"
        except RuntimeError as e:
            assert "selfbuild_recursive_invocation" in str(e)
    finally:
        engine._selfbuild_running = False


def test_selfbuild_diff_guard_detects_mismatch(tmp_path, monkeypatch):
    from shieldcraft.engine import Engine
    repo = tmp_path
    _prepare_repo_for_tests(repo)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)
    monkeypatch.chdir(repo)

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec = json.load(open(repo_root / "spec" / "se_dsl_v1.spec.json"))
    spec["metadata"]["spec_format"] = "canonical_json_v1"

    # Ensure self-build is enabled but baseline establishment is off (guard mode)
    monkeypatch.setenv('SHIELDCRAFT_SELFBUILD_ENABLED', '1')
    monkeypatch.delenv('SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE', raising=False)
    res = engine.run_self_build("spec/se_dsl_v1.spec.json", dry_run=False)
    out_dir = res.get("output_dir")

    # Corrupt emitted snapshot to simulate drift
    snap_path = os.path.join(out_dir, "repo_snapshot.json")
    snap = json.load(open(snap_path))
    snap["tree_hash"] = "deadbeef"
    open(snap_path, "w").write(json.dumps(snap, sort_keys=True))

    # Instead of invoking run_self_build again (which would overwrite outputs),
    # verify the corrupted output directly using the engine helper
    try:
        engine.verify_self_build_output(out_dir)
        assert False, "Expected selfbuild_mismatch"
    except RuntimeError as e:
        assert "selfbuild_mismatch" in str(e)
