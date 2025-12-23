import json
import hashlib
import os
from shieldcraft.services.sync import verify_repo_state_authoritative


def test_compare_authority_parity(tmp_path, monkeypatch):
    # Create repo and generate snapshot manifest
    from shieldcraft.snapshot import generate_snapshot
    m = generate_snapshot(str(tmp_path))
    # write canonical manifest into artifacts/repo_sync_state.json and record its sha
    os.makedirs(tmp_path / "artifacts", exist_ok=True)
    artifact_path = tmp_path / "artifacts" / "repo_sync_state.json"
    with open(artifact_path, "w") as f:
        json.dump(m, f, sort_keys=True)
    # compute sha of artifact file
    h = hashlib.sha256(open(artifact_path, "rb").read()).hexdigest()
    # write repo_state_sync.json
    repo_state = {"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}
    with open(tmp_path / "repo_state_sync.json", "w") as f:
        json.dump(repo_state, f)

    # compute expected manifest hash and assert equality with artifact sha
    from shieldcraft.services.sync import _canonical_manifest_hash
    manifest_hash = _canonical_manifest_hash(m)
    assert manifest_hash == h

    # sanity check: external artifact reads back as identical manifest
    with open(artifact_path) as af:
        external_manifest = json.load(af)
    from shieldcraft.services.sync import _canonical_manifest_hash
    assert _canonical_manifest_hash(external_manifest) == manifest_hash

    # Set authority to compare (use monkeypatch via os.environ for simple test)
    monkeypatch.setenv("SHIELDCRAFT_SYNC_AUTHORITY", "compare")

    res = verify_repo_state_authoritative(str(tmp_path))
    assert res.get("ok") is True
    assert res.get("authority") == "compare"


def test_sync_authority_compare(tmp_path, monkeypatch):
    # Thin wrapper to provide the exact test name required by CI's guard
    from shieldcraft.snapshot import generate_snapshot
    m = generate_snapshot(str(tmp_path))
    os.makedirs(tmp_path / "artifacts", exist_ok=True)
    artifact_path = tmp_path / "artifacts" / "repo_sync_state.json"
    with open(artifact_path, "w") as f:
        json.dump(m, f, sort_keys=True)
    h = hashlib.sha256(open(artifact_path, "rb").read()).hexdigest()
    repo_state = {"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}
    with open(tmp_path / "repo_state_sync.json", "w") as f:
        json.dump(repo_state, f)

    from shieldcraft.services.sync import _canonical_manifest_hash, verify_repo_state_authoritative
    assert _canonical_manifest_hash(m) == h

    monkeypatch.setenv("SHIELDCRAFT_SYNC_AUTHORITY", "compare")

    res = verify_repo_state_authoritative(str(tmp_path))
    assert res.get("ok") is True
    assert res.get("authority") == "compare"
