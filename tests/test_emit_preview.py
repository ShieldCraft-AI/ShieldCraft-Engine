import tempfile
import json
import os
import subprocess
import pytest


def test_emit_preview_with_schema_error():
    """Test that --emit-preview writes a file even when schema validation fails."""
    # Create an invalid spec (invalid metadata type)
    spec_content = {
        "metadata": "invalid_type",
        "self_host": True,
        "requirements": []
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as spec_file:
        json.dump(spec_content, spec_file)
        spec_file_path = spec_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as preview_file:
        preview_path = preview_file.name
    
    # Run CLI
    env = os.environ.copy()
    env["SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY"] = "1"
    result = subprocess.run([
        'python', '-m', 'shieldcraft.engine',
        '--self-host', spec_file_path,
        '--dry-run',
        '--emit-preview', preview_path
    ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/../..', env=env)
    # Assert exit code 0 (since dry-run returns preview)
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    
    # Assert file exists
    assert os.path.exists(preview_path), "Preview file was not created"
    
    # Assert valid JSON
    with open(preview_path, 'r') as f:
        data = json.load(f)
    assert isinstance(data, dict), "Preview is not a JSON object"
    
    # Assert error is present
    assert "validation_issues" in data or "validation_ok" in data, "Preview should contain validation info"
    assert data['validation_ok'] is False, "validation_ok should be False"