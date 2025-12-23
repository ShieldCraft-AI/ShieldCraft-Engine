import json
import os
import pytest


def test_execute_preflight_fails_fast(tmp_path):
    """Ensure engine.execute does not write plan files when validation fails."""
    from shieldcraft.engine import Engine
    from shieldcraft.services.validator import ValidationError

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Start from canonical spec and inject invalid instruction
    src = tmp_path / "spec.json"
    import pathlib
    data = json.loads(pathlib.Path("spec/se_dsl_v1.spec.json").read_text())
    data["metadata"]["spec_format"] = "canonical_json_v1"
    data["instructions"] = [{"id": "i1", "type": "t", "timestamp": "now"}]
    src.write_text(json.dumps(data))

    product_id = data["metadata"].get("product_id", "unknown")
    plan_dir = f"products/{product_id}"

    # Ensure no pre-existing plan dir
    if os.path.exists(plan_dir):
        import shutil

        shutil.rmtree(plan_dir)

    with pytest.raises(ValidationError):
        engine.execute(str(src))

    assert not os.path.exists(plan_dir), "Plan directory must not be created on validation failure"


def test_preflight_fails_on_missing_sync(tmp_path, monkeypatch):
    from shieldcraft.engine import Engine
    from shieldcraft.services.sync import SyncError

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # chdir to empty tmp so verify_repo_sync will not find repo_state_sync.json
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SyncError):
        engine.preflight({"metadata": {"product_id": "x"}, "model": {"version": "1.0"}, "sections": []})


def test_execute_no_side_effects_on_sync_failure(tmp_path, monkeypatch):
    from shieldcraft.engine import Engine
    from shieldcraft.services.sync import SyncError

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Use canonical sample spec to get past schema
    import pathlib
    import json
    data = json.loads(pathlib.Path("spec/se_dsl_v1.spec.json").read_text())
    data["metadata"]["spec_format"] = "canonical_json_v1"

    # write spec file into tmp directory before chdir
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(data))
    monkeypatch.chdir(tmp_path)

    product_id = data["metadata"].get("product_id", "unknown")
    plan_dir = f"products/{product_id}"

    with pytest.raises(SyncError):
        engine.execute(str(spec_path))

    assert not os.path.exists(plan_dir), "No artifacts should be written when sync verification fails"
