import tempfile
import json
import pytest


def test_engine_run_self_host_raises_on_invalid_instructions():
    """Engine.run_self_host must not bypass instruction validation."""
    from shieldcraft.engine import Engine
    from shieldcraft.services.validator import ValidationError

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Spec with ambient state in an instruction
    spec = {
        "metadata": {"product_id": "x", "self_host": True},
        "invariants": ["no ambient"],
        "instructions": [{"id": "i1", "type": "construction", "timestamp": "now"}],
    }

    with pytest.raises(ValidationError):
        engine.run_self_host(spec, dry_run=True)


def test_engine_execute_raises_on_invalid_instructions(tmp_path):
    from shieldcraft.engine import Engine
    from shieldcraft.services.validator import ValidationError

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Use an existing canonical spec as a baseline that passes schema validation,
    # then inject an invalid instruction to trigger the instruction validator.
    base = tmp_path / "base.spec.json"
    import pathlib
    src = pathlib.Path("spec/se_dsl_v1.spec.json")
    data = json.loads(src.read_text())
    # Ensure canonical metadata present
    data["metadata"]["spec_format"] = "canonical_json_v1"
    data["instructions"] = [{"id": "i1", "type": "construction", "timestamp": "now"}]

    spec_path = tmp_path / "bad.spec.json"
    spec_path.write_text(json.dumps(data))

    with pytest.raises(ValidationError):
        engine.execute(str(spec_path))
