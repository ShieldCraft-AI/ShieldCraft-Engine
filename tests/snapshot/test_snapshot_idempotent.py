from shieldcraft.snapshot import generate_snapshot


def test_snapshot_idempotent(tmp_path):
    # Create repo files
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("hello")
    f2.write_text("world")

    s1 = generate_snapshot(str(tmp_path))
    s2 = generate_snapshot(str(tmp_path))
    assert s1 == s2
    assert "tree_hash" in s1
