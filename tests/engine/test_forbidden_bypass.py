import json
import pytest


def test_engine_forbidden_bypass_run(monkeypatch, tmp_path):
    from shieldcraft.engine import Engine

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Use canonical sample and inject invalid instruction
    import pathlib
    data = json.loads(pathlib.Path("spec/se_dsl_v1.spec.json").read_text())
    data["metadata"]["spec_format"] = "canonical_json_v1"
    data["instructions"] = [{"id": "i1", "type": "construction", "timestamp": "now"}]

    spec_path = tmp_path / "bad.spec.json"
    spec_path.write_text(json.dumps(data))

    # Monkeypatch validation to no-op (simulated bypass) and assert engine detects it
    monkeypatch.setattr(engine, "_validate_spec", lambda spec: None)

    with pytest.raises(RuntimeError):
        engine.run(str(spec_path))


def test_forbidden_bypass_sync(monkeypatch, tmp_path):
    from shieldcraft.engine import Engine
    from shieldcraft.services.sync import SyncError

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Use canonical sample and inject invalid instruction
    import pathlib, json
    data = json.loads(pathlib.Path("spec/se_dsl_v1.spec.json").read_text())
    data["metadata"]["spec_format"] = "canonical_json_v1"
    data["instructions"] = [{"id": "i1", "type": "construction", "timestamp": "now"}]

    spec_path = tmp_path / "bad.spec.json"
    spec_path.write_text(json.dumps(data))

    # Monkeypatch verify_repo_sync to return an unexpected non-dict (simulate bypass)
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: None)

    # Execution should detect bypass and raise RuntimeError
    with pytest.raises(RuntimeError):
        engine.execute(str(spec_path))


def test_engine_forbidden_bypass_run_self_host(monkeypatch):
    from shieldcraft.engine import Engine

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    spec = {
        "metadata": {"product_id": "x", "self_host": True},
        "invariants": ["inv1"],
        "model": {"version": "1.0"},
        "sections": {},
        "instructions": [{"id": "i1", "type": "construction", "timestamp": "now"}],
    }

    monkeypatch.setattr(engine, "_validate_spec", lambda spec: None)

    with pytest.raises(RuntimeError):
        engine.run_self_host(spec, dry_run=True)
