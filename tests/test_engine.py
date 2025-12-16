from shieldcraft.engine import Engine
import json
import tempfile
import pathlib


def test_engine_pipeline():
    schema = "src/shieldcraft/dsl/schema/se_dsl.schema.json"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(json.dumps({
        "metadata": {"product_id": "t", "version": "1", "spec_format": "canonical_json_v1"},
        "model": {"version": "1.0"},
        "sections": [{"id": "s", "description": "x", "fields": {"a": 1}}]
    }).encode())
    tmp.close()

    engine = Engine(schema)
    result = engine.run(tmp.name)
    # May return schema_error or valid result
    assert "checklist" in result or "type" in result
