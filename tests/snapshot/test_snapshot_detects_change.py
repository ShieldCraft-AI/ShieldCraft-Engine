from shieldcraft.snapshot import generate_snapshot, write_snapshot, validate_snapshot, SnapshotError


def test_snapshot_detects_changes(tmp_path):
    f1 = tmp_path / "a.txt"
    f1.write_text("1")
    manifest = generate_snapshot(str(tmp_path))
    p = write_snapshot(manifest, path=str(tmp_path / "artifacts" / "repo_snapshot.json"))

    # Modify file
    f1.write_text("2")

    try:
        validate_snapshot(p, repo_root=str(tmp_path))
        assert False, "Expected SnapshotError"
    except SnapshotError as e:
        assert e.code == "snapshot_mismatch"
