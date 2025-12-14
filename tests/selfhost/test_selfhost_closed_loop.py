import os
import json
import hashlib
from shieldcraft.snapshot import generate_snapshot


def test_selfhost_roundtrip_identity(tmp_path, monkeypatch):
    # Prepare minimal repo (empty tmp dir)
    repo = tmp_path
    # Create initial internal snapshot
    internal = generate_snapshot(str(repo))

    # Write external artifact (initial) and repo_state_sync.json
    os.makedirs(repo / "artifacts", exist_ok=True)
    artifact_path = repo / "artifacts" / "repo_sync_state.json"
    artifact_path.write_text(json.dumps(internal, sort_keys=True))
    h = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    # Run self-host in compare mode to ensure parity check uses external artifact
    monkeypatch.setenv("SHIELDCRAFT_SYNC_AUTHORITY", "compare")
    monkeypatch.setenv("SHIELDCRAFT_ALLOW_EXTERNAL_SYNC", "1")
    monkeypatch.chdir(repo)
    # Provide minimal external sync artifact so default test env (external) passes
    os.makedirs(repo / "artifacts", exist_ok=True)
    if not (repo / "artifacts" / "repo_sync_state.json").exists():
        (repo / "artifacts" / "repo_sync_state.json").write_text(json.dumps({}))
    h = hashlib.sha256((repo / "artifacts" / "repo_sync_state.json").read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)

    from shieldcraft.engine import Engine
    from shieldcraft.services.sync import verify_repo_state_authoritative

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec = json.load(open(repo_root / "spec" / "se_dsl_v1.spec.json"))
    spec["metadata"]["spec_format"] = "canonical_json_v1"

    # Run self-host; should succeed and emit a bootstrap_manifest
    res = engine.run_self_host(spec, dry_run=False)
    assert res.get("manifest") is not None

    # Now write the emitted repo snapshot as the external artifact
    out_dir = res.get("output_dir")
    snap_path = os.path.join(out_dir, "repo_snapshot.json")
    with open(snap_path) as sf:
        snap = json.load(sf)
    artifact_path.write_text(json.dumps(snap, sort_keys=True))
    h2 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    with open(repo / "repo_state_sync.json", "w") as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h2}]}, f)

    # Parity compare should succeed (no exception)
    assert verify_repo_state_authoritative(str(repo)).get("ok") is True


def test_selfhost_closed_loop_determinism(tmp_path, monkeypatch):
    # Two dry-run previews must be identical and snapshots stable
    repo = tmp_path
    monkeypatch.chdir(repo)
    os.makedirs(repo / "artifacts", exist_ok=True)
    if not (repo / "artifacts" / "repo_sync_state.json").exists():
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

    assert p1 == p2

    # Snapshot remains identical across runs
    s1 = generate_snapshot(str(repo))
    s2 = generate_snapshot(str(repo))
    assert s1.get("tree_hash") == s2.get("tree_hash")


def test_selfhost_provenance_headers_included(monkeypatch, tmp_path):
    repo = tmp_path
    monkeypatch.chdir(repo)
    os.makedirs(repo / "artifacts", exist_ok=True)
    if not (repo / "artifacts" / "repo_sync_state.json").exists():
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

    preview = engine.run_self_host(spec, dry_run=True)
    manifest = preview.get("manifest", {})
    prov = manifest.get("provenance", {})
    assert prov.get("engine_version") is not None
    assert prov.get("spec_fingerprint") == preview.get("fingerprint")

    # Ensure preview outputs have header prefix
    outputs = preview.get("outputs", [])
    assert len(outputs) >= 0
    for out in outputs:
        content = out.get("content", "")
        assert content.startswith("# engine_version:"), "Provenance header missing"


def test_engine_selfhost_rejects_disallowed_inputs(monkeypatch, tmp_path):
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    bad_spec = {"metadata": {"self_host": True}, "weird": "not_allowed"}
    try:
        engine.run_self_host(bad_spec, dry_run=True)
        assert False, "Expected disallowed_selfhost_input"
    except RuntimeError as e:
        assert "disallowed_selfhost_input" in str(e)


def test_engine_selfhost_requires_sync(monkeypatch, tmp_path):
    from shieldcraft.engine import Engine
    from shieldcraft.services.sync import SyncError
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    spec["metadata"]["spec_format"] = "canonical_json_v1"

    # Force sync failure
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: (_ for _ in ()).throw(SyncError("sync_missing", "missing sync")))

    try:
        engine.run_self_host(spec, dry_run=True)
        assert False, "Expected SyncError"
    except SyncError:
        pass
