from shieldcraft.snapshot import generate_snapshot


def test_large_repo_sanity(tmp_path):
    # Create a larger synthetic tree (not too large for CI)
    for d in range(20):
        dirp = tmp_path / f"d{d}"
        dirp.mkdir()
        for f in range(20):
            (dirp / f"file{f}.txt").write_text(str(d * 100 + f))

    m = generate_snapshot(str(tmp_path))
    assert "tree_hash" in m
    assert len(m["files"]) >= 400
