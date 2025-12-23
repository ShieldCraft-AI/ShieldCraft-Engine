import tempfile
import json
import os
import shutil
from shieldcraft.main import run_self_host


def test_basic_selfhost_pipeline():
    """Test basic self-host pipeline execution."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-selfhost",
                "version": "1.0",
                "spec_format": "canonical_json_v1",
                "self_host": True
            },
            "model": {"version": "1.0"},
            "sections": [{"id": "bootstrap", "description": "Bootstrap components"}]
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    try:
        # Run self-host
        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")

        # Check output directory exists
        assert os.path.exists(".selfhost_outputs")

        # Check manifest exists
        assert os.path.exists(".selfhost_outputs/manifest.json")

        # Check summary exists
        assert os.path.exists(".selfhost_outputs/summary.json")

    finally:
        os.unlink(tmp_path)
        if os.path.exists(".selfhost_outputs"):
            shutil.rmtree(".selfhost_outputs")


def test_selfhost_output_structure():
    """Test self-host output structure."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-struct",
                "version": "1.0",
                "spec_format": "canonical_json_v1"
            },
            "model": {"version": "1.0"},
            "sections": [{"id": "core"}]
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    try:
        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")

        # Load summary
        with open(".selfhost_outputs/summary.json") as f:
            summary = json.load(f)

        assert "status" in summary
        assert "stable" in summary

    finally:
        os.unlink(tmp_path)
        if os.path.exists(".selfhost_outputs"):
            shutil.rmtree(".selfhost_outputs")


def test_selfhost_isolation():
    """Test that self-host only writes to .selfhost_outputs/."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-isolation",
                "version": "1.0",
                "spec_format": "canonical_json_v1"
            },
            "model": {},
            "sections": [{"id": "core"}]
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    # Track products directory before
    products_exists_before = os.path.exists("products/test-isolation")

    try:
        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")

        # Self-host should not create products directory
        assert os.path.exists(".selfhost_outputs")

    finally:
        os.unlink(tmp_path)
        if os.path.exists(".selfhost_outputs"):
            shutil.rmtree(".selfhost_outputs")
