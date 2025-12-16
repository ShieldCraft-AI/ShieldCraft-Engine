from shieldcraft.verification.test_to_artifact import check_orphan_artifacts


def test_orphan_artifacts_detected():
    artifacts = ["a.json", "b.json"]
    test_artifact_map = {"t1": ["a.json"]}

    v = check_orphan_artifacts(artifacts, test_artifact_map)
    assert len(v) == 1
    assert v[0]["artifact"] == "b.json"
    assert v[0]["reason"] == "orphan_artifact"
