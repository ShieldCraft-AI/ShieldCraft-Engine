import tempfile
import json
import os
import subprocess
import pytest


def test_emit_preview_creates_file():
    """Test that --emit-preview creates a preview file with valid JSON."""
    # Use a simple test spec
    spec_content = {
        "metadata": {
            "generator_version": "1.0.0",
            "spec_format": "canonical_v1_frozen"
        },
        "self_host": True,
        "requirements": [
            {"id": "test_req", "text": "Must have test", "category": "bootstrap"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as spec_file:
        json.dump(spec_content, spec_file)
        spec_file_path = spec_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as preview_file:
        preview_path = preview_file.name
    
    try:
        # Run CLI
        result = subprocess.run([
            'python', '-m', 'shieldcraft.main',
            '--self-host', spec_file_path,
            '--dry-run',
            '--emit-preview', preview_path
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/../..')
        
        # Assert exit code 0
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Assert file exists
        assert os.path.exists(preview_path), "Preview file was not created"
        
        # Assert valid JSON
        with open(preview_path, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict), "Preview is not a JSON object"
        
    finally:
        # Cleanup
        if os.path.exists(spec_file_path):
            os.unlink(spec_file_path)
        if os.path.exists(preview_path):
            os.unlink(preview_path)


def test_emit_preview_without_flag_no_file():
    """Test that without --emit-preview, no preview file is created."""
    spec_content = {
        "metadata": {
            "generator_version": "1.0.0",
            "spec_format": "canonical_v1_frozen"
        },
        "self_host": True,
        "requirements": [
            {"id": "test_req", "text": "Must have test", "category": "bootstrap"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as spec_file:
        json.dump(spec_content, spec_file)
        spec_file_path = spec_file.name
    
    preview_path = "/tmp/nonexistent_preview.json"
    
    try:
        # Run CLI without --emit-preview
        result = subprocess.run([
            'python', '-m', 'shieldcraft.main',
            '--self-host', spec_file_path
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/../..')
        
        # Assert exit code 0
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Assert file does not exist
        assert not os.path.exists(preview_path), "Preview file was created unexpectedly"
        
    finally:
        # Cleanup
        if os.path.exists(spec_file_path):
            os.unlink(spec_file_path)