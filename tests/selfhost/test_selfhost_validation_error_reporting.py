import json
import os
import tempfile


def test_selfhost_writes_structured_validation_errors():
    """When instruction validation fails, self-host should write errors.json."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-validation-error",
                "version": "1.0",
                "spec_format": "canonical_json_v1",
                "self_host": True,
            },
            "sections": [{"id": "core"}],
            "invariants": ["No ambient"],
            "instructions": [
                {"id": "i1", "type": "construction", "timestamp": "2025-12-14T00:00:00Z"}
            ],
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    try:
        # Clean output directory
        if os.path.exists(".selfhost_outputs"):
            import shutil

            shutil.rmtree(".selfhost_outputs")

        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")

        # Verify errors.json exists and contains structured ValidationError
        err_path = os.path.join(".selfhost_outputs", "errors.json")
        assert os.path.exists(err_path), "errors.json not written"

        with open(err_path) as f:
            data = json.load(f)

        assert "errors" in data and isinstance(data["errors"], list)
        assert data["errors"][0]["code"] in ("ambient_state", "sections_empty")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_selfhost_errors_are_deterministic_across_runs():
    """Repeated self-host runs with identical invalid spec produce identical errors.json."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-validation-error-2",
                "version": "1.0",
                "spec_format": "canonical_json_v1",
                "self_host": True,
            },
            "invariants": [{"id": "inv.1", "rule": "true"}],
            "model": {"version": "1.0"},
            "sections": {},
            "instructions": [
                {"id": "i1", "type": "construction", "timestamp": "2025-12-14T00:00:00Z"}
            ],
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    try:
        # Run twice and compare errors
        if os.path.exists(".selfhost_outputs"):
            import shutil

            shutil.rmtree(".selfhost_outputs")

        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")
        p1 = os.path.join(".selfhost_outputs", "errors.json")
        assert os.path.exists(p1)
        with open(p1) as f:
            d1 = json.load(f)

        # Clean and run again
        if os.path.exists(".selfhost_outputs"):
            import shutil

            shutil.rmtree(".selfhost_outputs")

        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")
        p2 = os.path.join(".selfhost_outputs", "errors.json")
        assert os.path.exists(p2)
        with open(p2) as f:
            d2 = json.load(f)

        assert d1 == d2

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
