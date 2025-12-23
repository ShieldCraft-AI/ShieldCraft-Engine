from shieldcraft.services.preflight.preflight import run_preflight


def test_preflight_basic():
    spec = {"metadata": {"a": 1}, "api": {}}
    schema = {"type": "object"}
    items = [{"ptr": "/metadata/a", "text": "x", "id": "test1"}]
    result = run_preflight(spec, schema, items)
    assert "schema_valid" in result
    assert "uncovered_ptrs" in result
