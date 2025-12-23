import json


def test_engine_is_in_compatibility_matrix():
    data = json.load(open("compatibility_matrix.json", encoding='utf-8'))
    engine_version = data.get("engine_version")
    assert engine_version == "0.1.0"
    assert any(entry for entry in data.get("compatibility", []) if entry.get("engine") == engine_version)
