import pytest
import json
import tempfile
from shieldcraft.engine import Engine
from shieldcraft.services.validator import ValidationError


def test_engine_rejects_missing_invariants():
    schema = "src/shieldcraft/dsl/schema/se_dsl.schema.json"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {
            "metadata": {"product_id": "test_e2e", "version": "1.0", "spec_version": "1"},
            "instructions": [{"id": "s1", "type": "verification"}],
            "model": {"version": "1.0"},
            "sections": []
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    engine = Engine(schema)
    with pytest.raises(ValidationError):
        engine.run(tmp_path)


def test_engine_accepts_valid_instructions():
    schema = "src/shieldcraft/dsl/schema/se_dsl.schema.json"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {
            "metadata": {"product_id": "test_e2e", "version": "1.0", "spec_version": "1"},
            "invariants": ["No ambient state"],
            "instructions": [{"id": "s1", "type": "verification"}],
            "model": {"version": "1.0"},
            "sections": []
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    engine = Engine(schema)
    # Should not raise
    engine.run(tmp_path)
