import json
import jsonschema


def normalize_spec(spec):
    """
    Normalize spec for deterministic comparison.
    
    Operations:
    - Sort all dict keys recursively
    - Canonicalize values (strip whitespace from strings)
    - Sort lists of dicts by 'id' field if present
    
    Returns:
        Normalized spec dict
    """
    if isinstance(spec, dict):
        normalized = {}
        for key in sorted(spec.keys()):
            normalized[key] = normalize_spec(spec[key])
        return normalized
    
    elif isinstance(spec, list):
        # Check if list contains dicts with 'id' field
        if spec and isinstance(spec[0], dict) and 'id' in spec[0]:
            # Sort by id
            sorted_list = sorted(spec, key=lambda x: x.get('id', ''))
            return [normalize_spec(item) for item in sorted_list]
        else:
            return [normalize_spec(item) for item in spec]
    
    elif isinstance(spec, str):
        # Strip leading/trailing whitespace
        return spec.strip()
    
    else:
        return spec


def validate_spec_against_schema(spec, schema):
    """
    Validate spec dict using provided JSON Schema.
    Returns (valid: bool, errors: list[str]).
    """
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(spec), key=lambda e: e.path)
    if errors:
        return False, [f"{'.'.join([str(p) for p in e.path])}: {e.message}" for e in errors]
    return True, []
