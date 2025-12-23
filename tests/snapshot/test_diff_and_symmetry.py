from shieldcraft.snapshot import generate_snapshot, diff_snapshots


def test_snapshot_diff_symmetry(tmp_path):
    # Setup repo A
    a = tmp_path / "repoA"
    b = tmp_path / "repoB"
    a.mkdir()
    b.mkdir()

    (a / "x.txt").write_text("1")
    (a / "y.txt").write_text("2")

    (b / "x.txt").write_text("1")
    (b / "z.txt").write_text("3")

    ma = generate_snapshot(str(a))
    mb = generate_snapshot(str(b))

    d_ab = diff_snapshots(ma, mb)
    d_ba = diff_snapshots(mb, ma)

    assert set(d_ab["added"]) == set(d_ba["removed"])
    assert set(d_ab["removed"]) == set(d_ba["added"])
    # changed should be symmetric
    assert len(d_ab["changed"]) == len(d_ba["changed"]) == 0
