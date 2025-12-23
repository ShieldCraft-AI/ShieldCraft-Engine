import json
import os
import tempfile


def test_selfhost_writes_suppressed_signal_report_on_validation_failure():
    """When validation fails but pre-scan finds obligation prose, write suppressed report."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-suppressed-1",
                "version": "1.0",
                "spec_format": "canonical_json_v1",
                "self_host": True,
            },
            # Intentionally invalid shape to trigger validation failure
            "description": "This product must never allow ambient leaks.",
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    try:
        if os.path.exists(".selfhost_outputs"):
            import shutil

            shutil.rmtree(".selfhost_outputs")

        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")

        sup_path = os.path.join(".selfhost_outputs", "suppressed_signal_report.json")
        assert os.path.exists(sup_path), "suppressed_signal_report.json not written"

        with open(sup_path) as f:
            data = json.load(f)
        assert "suppressed" in data and isinstance(data["suppressed"], list)

        summary_path = os.path.join(".selfhost_outputs", "summary.json")
        assert os.path.exists(summary_path), "summary.json not written"
        with open(summary_path) as f:
            s = json.load(f)
        assert s.get("suppressed_signal_count") == len(data.get("suppressed", []))
        assert "inferred_from_prose_count" in s
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
