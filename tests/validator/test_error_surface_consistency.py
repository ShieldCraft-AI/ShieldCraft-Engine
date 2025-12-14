import json
import os
import tempfile
import pytest


def test_error_surface_consistency_across_paths():
    """Ensure preflight, validator and CLI self-host errors surface identically."""
    from shieldcraft.engine import Engine
    from shieldcraft.services.validator import ValidationError
    from shieldcraft.main import run_self_host

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    import pathlib
    spec = json.loads(pathlib.Path("spec/se_dsl_v1.spec.json").read_text())
    spec["metadata"]["spec_format"] = "canonical_json_v1"
    spec["instructions"] = [{"id": "i1", "type": "construction", "timestamp": "now"}]

    # Engine preflight raises ValidationError
    with pytest.raises(ValidationError) as e:
        engine.preflight(spec)
    pre = e.value.to_dict()

    # Validator direct call
    with pytest.raises(ValidationError) as e2:
        from shieldcraft.services.validator import validate_instruction_block

        validate_instruction_block(spec)
    val = e2.value.to_dict()

    # CLI self-host writes errors.json
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
        json.dump(spec, tmp)
        tmp_path = tmp.name

    try:
        if os.path.exists(".selfhost_outputs"):
            import shutil

            shutil.rmtree(".selfhost_outputs")
        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")
        err_path = os.path.join(".selfhost_outputs", "errors.json")
        assert os.path.exists(err_path)
        with open(err_path) as f:
            cli = json.load(f)["errors"][0]

        assert pre == val == cli
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
