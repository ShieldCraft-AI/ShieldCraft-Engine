import json
from shieldcraft.snapshot import validate_snapshot, SNAPSHOT_INVALID, SnapshotError


def test_unknown_version_guard(tmp_path):
    manifest = {"version": "v2", "hash_algorithm": "sha256", "files": [], "tree_hash": "abc"}
    path = tmp_path / "artifacts" / "repo_snapshot.json"
    path.parent.mkdir()
    with open(path, "w") as f:
        json.dump(manifest, f)

    try:
        validate_snapshot(str(path), repo_root=str(tmp_path))
        assert False, "Expected SnapshotError for unknown version"
    except SnapshotError as e:
        assert e.code == SNAPSHOT_INVALID
