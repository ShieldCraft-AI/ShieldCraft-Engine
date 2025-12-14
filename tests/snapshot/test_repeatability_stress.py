from shieldcraft.snapshot import generate_snapshot


def test_snapshot_repeatability_stress(tmp_path):
    # Create many files
    for i in range(50):
        d = tmp_path / f"dir{i % 5}"
        d.mkdir(exist_ok=True)
        (d / f"f{i}.txt").write_text(str(i))

    first = generate_snapshot(str(tmp_path))
    for _ in range(10):
        curr = generate_snapshot(str(tmp_path))
        assert curr["tree_hash"] == first["tree_hash"]
