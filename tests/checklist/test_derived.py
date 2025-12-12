from shieldcraft.services.checklist.derived import infer_tasks


def test_infer_tasks_empty():
    item = {"ptr": "/test", "text": "test"}
    result = infer_tasks(item)
    assert isinstance(result, list)


def test_infer_tasks_missing_metadata():
    item = {
        "ptr": "/metadata",
        "text": "metadata",
        "value": {"name": "test"}
    }
    result = infer_tasks(item)
    assert len(result) >= 2  # missing product_id and version
    assert any("product_id" in t["ptr"] for t in result)
    assert any("version" in t["ptr"] for t in result)


def test_infer_tasks_dependencies():
    item = {
        "ptr": "/feature",
        "text": "feature",
        "value": {"dependencies": ["dep1", "dep2"]},
        "classification": "features"
    }
    result = infer_tasks(item)
    assert len(result) >= 2
    assert all("id" in t for t in result)
