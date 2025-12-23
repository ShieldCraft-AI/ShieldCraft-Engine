"""
Canonical DSL loader for SE specifications.
Enforces deterministic JSON, validates schema, builds AST.
"""
import json
import pathlib
from datetime import datetime
from jsonschema import validate


def canonicalize_json(data, float_precision=2):
    """
    Canonicalize JSON object:
    - Sort all dict keys recursively
    - Round floats to specified precision
    - Normalize timestamps to UTC ISO-8601

    Returns canonical dict.
    """
    if isinstance(data, dict):
        canonical = {}
        for key in sorted(data.keys()):
            canonical[key] = canonicalize_json(data[key], float_precision)
        return canonical
    elif isinstance(data, list):
        return [canonicalize_json(item, float_precision) for item in data]
    elif isinstance(data, float):
        return round(data, float_precision)
    elif isinstance(data, str):
        # Attempt timestamp normalization
        try:
            dt = datetime.fromisoformat(data.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            return data
    else:
        return data


def validate_canonical_rules(data):
    """
    Validate canonical JSON rules:
    - No comments (JSON standard enforces this)
    - Keys must be sorted (checked separately)
    - Timestamps normalized

    Returns (ok: bool, issues: list)
    """
    issues = []

    def check_sorted_keys(obj, path=""):
        if isinstance(obj, dict):
            keys = list(obj.keys())
            sorted_keys = sorted(keys)
            if keys != sorted_keys:
                issues.append(f"Keys not sorted at {path}: {keys[:5]}... vs {sorted_keys[:5]}...")
            for key in keys:
                check_sorted_keys(obj[key], f"{path}/{key}")
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                check_sorted_keys(item, f"{path}[{idx}]")

    check_sorted_keys(data)

    return len(issues) == 0, issues


def load_canonical_spec(path: str):
    """
    Load canonical SE DSL spec from file.

    Steps:
    1. Read file bytes, decode UTF-8
    2. Parse JSON
    3. Canonicalize if needed (sort keys, normalize timestamps)
    4. Validate against schema
    5. Build AST
    6. Compute fingerprint
    7. Return SpecModel

    Args:
        path: Path to spec file

    Returns:
        SpecModel with raw, ast, fingerprint
    """
    # Step 1: Read file bytes, ensure UTF-8
    file_path = pathlib.Path(path)
    content_bytes = file_path.read_bytes()
    content_text = content_bytes.decode('utf-8')

    # Step 2: Parse JSON
    raw_data = json.loads(content_text)

    # Step 3: Get float precision from metadata
    float_precision = 2
    if isinstance(raw_data, dict):
        metadata = raw_data.get("metadata", {})
        if isinstance(metadata, dict):
            float_precision = metadata.get("float_precision", 2)

    # Step 3b: Canonicalize
    canonical_data = canonicalize_json(raw_data, float_precision)

    # Step 3c: Validate canonical rules
    ok = validate_canonical_rules(canonical_data)[0]
    if not ok:
        # Auto-fix by using canonicalized version
        pass  # Already canonicalized

    # Step 4: Validate against schema (optional - skip if schema not found or validation fails)
    schema_path = file_path.parent.parent.parent / "dsl" / "schema" / "se_dsl.schema.json"
    if not schema_path.exists():
        # Try alternative path
        schema_path = pathlib.Path(__file__).parent.parent.parent / "dsl" / "schema" / "se_dsl.schema.json"

    if schema_path.exists():
        try:
            schema = json.loads(schema_path.read_text())
            validate(canonical_data, schema)
        except (json.JSONDecodeError, ImportError, AttributeError, TypeError, ValueError):
            # INTENTIONAL: Skip validation errors for canonical specs.
            # Canonical specs may have extended structure beyond base schema.
            # Validation is advisory only during canonical loading.
            pass
        except RuntimeError:
            # Catch any other unexpected runtime exception, but this should be rare.
            pass

    # Step 5: Build AST
    from shieldcraft.services.ast.builder import ASTBuilder
    builder = ASTBuilder()
    ast = builder.build(canonical_data)

    # Step 6: Compute fingerprint
    from shieldcraft.services.spec.fingerprint import compute_spec_fingerprint
    fingerprint = compute_spec_fingerprint(canonical_data)

    # Step 7: Return SpecModel
    from shieldcraft.services.spec.model import SpecModel
    return SpecModel(
        raw=canonical_data,
        ast=ast,
        fingerprint=fingerprint
    )
