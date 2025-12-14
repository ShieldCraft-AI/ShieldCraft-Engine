import os
from shieldcraft.snapshot import write_snapshot, DEFAULT_SNAPSHOT_PATH


def test_snapshot_writes_to_locked_location(tmp_path):
    manifest = {"version": "v1", "hash_algorithm": "sha256", "files": [], "tree_hash": "abc"}
    path = write_snapshot(manifest, path=str(tmp_path / DEFAULT_SNAPSHOT_PATH))
    assert os.path.exists(path)
    # Ensure no other snapshot-like files written at root
    root_snapshot = tmp_path / "repo_snapshot.json"
    assert not root_snapshot.exists()
