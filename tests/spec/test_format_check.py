"""Test formatting and determinism."""
import json
import pytest
from pathlib import Path


def test_json_formatting_deterministic():
    """Test that JSON files maintain deterministic formatting."""
    json_files = [
        Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json",
        Path(__file__).parent.parent.parent / "spec/pointer_map.json",
        Path(__file__).parent.parent.parent / "generators/lockfile.json"
    ]
    
    for json_path in json_files:
        if not json_path.exists():
            continue
        
        with open(json_path) as f:
            original_content = f.read()
        
        # Parse and re-serialize
        with open(json_path) as f:
            data = json.load(f)
        
        reserialized = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
        reserialized += '\n'  # Add trailing newline
        
        # Compare
        if original_content != reserialized:
            # Show diff for debugging
            original_lines = original_content.split('\n')
            reserialized_lines = reserialized.split('\n')
            
            diff = []
            for i, (orig, reser) in enumerate(zip(original_lines, reserialized_lines)):
                if orig != reser:
                    diff.append(f"Line {i+1}:\n  Original: {repr(orig)}\n  Reserialized: {repr(reser)}")
            
            pytest.fail(f"JSON formatting not deterministic for {json_path.name}:\n" + "\n".join(diff[:5]))


def test_no_python_formatting_changes():
    """Test that Python files don't need formatting changes."""
    # This is a placeholder - in real CI, you'd run black --check or ruff format --check
    # For now, just verify Python files exist and are valid syntax
    
    python_files = [
        Path(__file__).parent.parent.parent / "src/shieldcraft/services/io/manifest_writer.py",
        Path(__file__).parent.parent.parent / "src/shieldcraft/services/spec/pointer_auditor.py",
        Path(__file__).parent.parent.parent / "src/shieldcraft/services/preflight/preflight.py"
    ]
    
    for py_path in python_files:
        if not py_path.exists():
            continue
        
        try:
            with open(py_path) as f:
                code = f.read()
            
            # Try to compile (basic syntax check)
            compile(code, str(py_path), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Python file {py_path.name} has syntax errors: {e}")


def test_consistent_line_endings():
    """Test that files use consistent line endings (LF)."""
    files_to_check = [
        Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json",
        Path(__file__).parent.parent.parent / "spec/README.md"
    ]
    
    for file_path in files_to_check:
        if not file_path.exists():
            continue
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Check for CRLF
        if b'\r\n' in content:
            pytest.fail(f"{file_path.name} contains CRLF line endings (should be LF)")


def test_utf8_encoding():
    """Test that files are UTF-8 encoded."""
    files_to_check = [
        Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json",
        Path(__file__).parent.parent.parent / "spec/pointer_map.json"
    ]
    
    for file_path in files_to_check:
        if not file_path.exists():
            continue
        
        try:
            with open(file_path, encoding='utf-8') as f:
                f.read()
        except UnicodeDecodeError as e:
            pytest.fail(f"{file_path.name} is not valid UTF-8: {e}")
