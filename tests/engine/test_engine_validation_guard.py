import json
import pytest


def test_generate_code_enforces_instruction_validation(tmp_path):
    from shieldcraft.engine import Engine
    from shieldcraft.services.validator import ValidationError

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Use canonical sample and inject an invalid instruction
    import pathlib
    src = pathlib.Path("spec/se_dsl_v1.spec.json")
    data = json.loads(src.read_text())
    data["metadata"]["spec_format"] = "canonical_json_v1"
    data["instructions"] = [{"id": "i1", "type": "construction", "timestamp": "now"}]

    tmpf = tmp_path / "tmp.spec.json"
    tmpf.write_text(json.dumps(data))

    with pytest.raises(ValidationError):
        engine.generate_code(str(tmpf), dry_run=True)
