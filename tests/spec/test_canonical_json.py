"""Test canonical JSON serialization."""
import json
import hashlib
from pathlib import Path


def test_canonical_json_determinism():
    """Test that spec serializes deterministically via canonical JSON."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"

    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    # Serialize via canonical JSON (sort_keys=True)
    serialized1 = json.dumps(spec, sort_keys=True, indent=None, separators=(',', ':'))
    hash1 = hashlib.sha256(serialized1.encode()).hexdigest()

    # Re-serialize
    serialized2 = json.dumps(spec, sort_keys=True, indent=None, separators=(',', ':'))
    hash2 = hashlib.sha256(serialized2.encode()).hexdigest()

    # Assert identical hashes
    assert hash1 == hash2, "Canonical JSON serialization is not deterministic"


def test_canonical_json_key_ordering():
    """Test that canonical JSON maintains key ordering."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"

    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    # Serialize with sort_keys
    serialized = json.dumps(spec, sort_keys=True, indent=2)

    # Verify top-level keys are sorted
    lines = serialized.split('\n')
    top_level_keys = []

    for line in lines:
        if line.strip().startswith('"') and '":' in line:
            key = line.strip().split('"')[1]
            if line.startswith('  "'):  # Top-level key (2 spaces indent)
                top_level_keys.append(key)

    # Check if sorted
    assert top_level_keys == sorted(top_level_keys), f"Top-level keys not sorted: {top_level_keys}"


def test_canonical_json_no_trailing_whitespace():
    """Test that canonical JSON has no trailing whitespace."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"

    with open(spec_path, encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    trailing_whitespace_lines = []
    for idx, line in enumerate(lines):
        if line.endswith(' ') or line.endswith('\t'):
            trailing_whitespace_lines.append(idx + 1)

    assert len(trailing_whitespace_lines) == 0, f"Lines with trailing whitespace: {trailing_whitespace_lines}"


def test_canonical_json_consistent_indentation():
    """Test that JSON uses consistent indentation."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"

    with open(spec_path, encoding='utf-8') as f:
        content = f.read()

    # Check for tabs
    assert '\t' not in content, "Spec contains tab characters"

    # Verify consistent 2-space indentation
    lines = content.split('\n')
    for idx, line in enumerate(lines):
        if line and not line.strip().startswith('//'):
            leading_spaces = len(line) - len(line.lstrip(' '))
            if leading_spaces > 0:
                assert leading_spaces % 2 == 0, f"Line {idx + 1} has inconsistent indentation: {leading_spaces} spaces"
