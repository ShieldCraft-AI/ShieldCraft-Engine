"""
Test validate-spec CLI command.
"""

import json
import os
import tempfile
import subprocess
import sys


def test_validate_spec_valid_spec():
    """Test validate-spec with a valid spec."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create valid spec
        spec = {
            "version": "1.0",
            "sections": [
                {
                    "id": "section1",
                    "tasks": [
                        {
                            "id": "task1",
                            "description": "Test task",
                            "lineage_id": "LIN001"
                        }
                    ]
                }
            ]
        }
        spec_path = os.path.join(tmpdir, "spec.json")
        with open(spec_path, "w") as f:
            json.dump(spec, f)

        # Create minimal schema
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["version", "sections"],
            "properties": {
                "version": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "tasks"],
                        "properties": {
                            "id": {"type": "string"},
                            "tasks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id", "description"],
                                    "properties": {
                                        "id": {"type": "string"},
                                        "description": {"type": "string"},
                                        "lineage_id": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        schema_path = os.path.join(tmpdir, "schema.json")
        with open(schema_path, "w") as f:
            json.dump(schema, f)

        # Run validate-spec
        result = subprocess.run(
            [sys.executable, "-m", "shieldcraft.main", "--validate-spec", spec_path, "--schema", schema_path],
            capture_output=True,
            text=True
        )

        # Should succeed
        assert result.returncode == 0
        assert "✓ Spec is valid" in result.stdout


def test_validate_spec_invalid_spec():
    """Test validate-spec with an invalid spec (missing required field)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create invalid spec (missing version)
        spec = {
            "sections": [
                {
                    "id": "section1",
                    "tasks": []
                }
            ]
        }
        spec_path = os.path.join(tmpdir, "spec.json")
        with open(spec_path, "w") as f:
            json.dump(spec, f)

        # Create schema requiring version
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["version", "sections"],
            "properties": {
                "version": {"type": "string"},
                "sections": {"type": "array"}
            }
        }
        schema_path = os.path.join(tmpdir, "schema.json")
        with open(schema_path, "w") as f:
            json.dump(schema, f)

        # Run validate-spec
        result = subprocess.run(
            [sys.executable, "-m", "shieldcraft.main", "--validate-spec", spec_path, "--schema", schema_path],
            capture_output=True,
            text=True
        )

        # Should fail
        assert result.returncode == 1
        assert "✗ Spec validation failed" in result.stdout
        assert "Schema Errors" in result.stdout
