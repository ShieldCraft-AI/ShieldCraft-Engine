import json
import os
import shutil
import tempfile
import pytest
from shieldcraft.services.sync import verify_repo_sync, SyncError, SYNC_MISSING, SYNC_HASH_MISMATCH
from shieldcraft.services.sync import REPO_STATE_FILENAME, REPO_SYNC_ARTIFACT, SYNC_TREE_MISMATCH


def _copy_artifact(src_path, dst_root, rel_path):
    dst = os.path.join(dst_root, rel_path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src_path, dst)


def test_verify_repo_sync_missing_file(tmp_path):
    # empty dir
    with pytest.raises(SyncError) as e:
        verify_repo_sync(str(tmp_path))
    assert e.value.code == SYNC_MISSING


def test_verify_repo_sync_stale_hash(tmp_path):
    # create artifact and repo_state_sync.json with wrong sha
    artifact_content = b"hello"
    art_path = tmp_path / "artifacts" / "repo_sync_state.json"
    art_path.parent.mkdir(parents=True, exist_ok=True)
    art_path.write_bytes(artifact_content)

    repo_state = {
        "files": [
            {"path": "artifacts/repo_sync_state.json", "sha256": "deadbeef"}
        ]
    }
    (tmp_path / "repo_state_sync.json").write_text(json.dumps(repo_state))

    with pytest.raises(SyncError) as e:
        verify_repo_sync(str(tmp_path))
    assert e.value.code == SYNC_HASH_MISMATCH


def test_verify_repo_sync_tree_mismatch(tmp_path):
    # create artifact and repo_state_sync.json with correct sha but wrong tree hash
    artifact_content = b"hello"
    art_path = tmp_path / "artifacts" / "repo_sync_state.json"
    art_path.parent.mkdir(parents=True, exist_ok=True)
    art_path.write_bytes(artifact_content)

    actual_sha = (art_path).read_bytes()
    import hashlib
    sha = hashlib.sha256(artifact_content).hexdigest()

    repo_state = {
        "files": [
            {"path": REPO_SYNC_ARTIFACT, "sha256": sha}
        ],
        "repo_tree_hash": "deadbeef"
    }
    (tmp_path / REPO_STATE_FILENAME).write_text(json.dumps(repo_state))

    with pytest.raises(SyncError) as e:
        verify_repo_sync(str(tmp_path))
    assert e.value.code == SYNC_TREE_MISMATCH


def test_verify_repo_sync_passes(tmp_path):
    # copy existing repo_state_sync.json and referenced artifact into tmp
    root = os.getcwd()
    src_sync = os.path.join(root, "repo_state_sync.json")
    assert os.path.exists(src_sync)

    with open(src_sync) as f:
        data = json.load(f)

    # find artifact entry
    entry = None
    for ent in data.get("files", []):
        if ent.get("path") == "artifacts/repo_sync_state.json":
            entry = ent
            break
    assert entry is not None and "sha256" in entry

    # copy file referenced
    _copy_artifact(os.path.join(root, entry["path"]), str(tmp_path), entry["path"])
    # write repo_state_sync.json with same entry
    (tmp_path / "repo_state_sync.json").write_text(json.dumps({"files": [entry]}))

    res = verify_repo_sync(str(tmp_path))
    assert res["ok"] is True
    assert res["artifact"] == "artifacts/repo_sync_state.json"


def test_verify_repo_sync_deterministic(tmp_path):
    # Create artifact and repo_state_sync.json correctly, then run twice
    artifact_content = b"hello"
    art_path = tmp_path / "artifacts" / "repo_sync_state.json"
    art_path.parent.mkdir(parents=True, exist_ok=True)
    art_path.write_bytes(artifact_content)

    import hashlib
    sha = hashlib.sha256(artifact_content).hexdigest()

    repo_state = {
        "files": [
            {"path": REPO_SYNC_ARTIFACT, "sha256": sha}
        ]
    }
    (tmp_path / REPO_STATE_FILENAME).write_text(json.dumps(repo_state))

    r1 = verify_repo_sync(str(tmp_path))
    r2 = verify_repo_sync(str(tmp_path))

    assert r1 == r2
