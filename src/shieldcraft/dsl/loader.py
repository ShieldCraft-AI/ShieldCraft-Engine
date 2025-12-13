"""
Canonical DSL loader for ShieldCraft Engine.
Exclusively loads canonical JSON specs.
"""
import json
import pathlib
import logging
from shieldcraft.dsl.canonical_loader import load_canonical_spec

logger = logging.getLogger(__name__)

# Required canonical DSL version
_DSL_VERSION_REQUIRED = "canonical_v1_frozen"


def load_spec(path):
    """
    Load spec from path using canonical loader.
    Returns SpecModel for canonical specs or raw dict for legacy.
    
    AUTHORITY: Enforces dsl_version == canonical_v1_frozen.
    """
    file_path = pathlib.Path(path)
    data = json.loads(file_path.read_text())
    
    # Enforce DSL version from top-level or metadata spec_format when explicitly present.
    # If neither is present, treat as a legacy spec and return raw data (no hard failure).
    dsl_version = data.get('dsl_version')
    spec_format = data.get('metadata', {}).get('spec_format')

    if dsl_version:
        if dsl_version != _DSL_VERSION_REQUIRED:
            raise ValueError(
                f"DSL version mismatch: expected '{_DSL_VERSION_REQUIRED}', "
                f"got '{dsl_version}'. Spec must use canonical DSL v1 frozen."
            )
    elif spec_format:
        if spec_format == 'canonical_json_v1':
            dsl_version = 'canonical_v1_frozen'
        else:
            # Non-canonical spec_format specified: treat as explicit mismatch.
            raise ValueError(
                f"Unsupported spec_format '{spec_format}'; expected canonical_json_v1 or omit to use legacy format."
            )
    else:
        # No dsl_version and no spec_format: legacy spec; return raw data but log deprecation.
        logger.warning(f"DEPRECATION: old DSL format detected at {path}; treat as legacy and migrate to canonical JSON.")
        return data
    
    # Detect canonical vs legacy
    if isinstance(data, dict) and ('canonical' in data or 'canonical_spec_hash' in data.get('metadata', {})):
        return load_canonical_spec(path)
    else:
        logger.warning(f"DEPRECATION: old DSL format in use at {path}; migrate to canonical JSON.")
        # Return raw data for legacy
        return data


def extract_json_pointers(spec, base=""):
    """
    Recursively extract JSON Pointer paths from spec.
    Output: set of pointer strings.
    """
    out = set()

    if isinstance(spec, dict):
        for k, v in spec.items():
            new_ptr = f"{base}/{k}"
            out.add(new_ptr)
            out |= extract_json_pointers(v, new_ptr)
        return out

    if isinstance(spec, list):
        for idx, v in enumerate(spec):
            new_ptr = f"{base}/{idx}"
            out.add(new_ptr)
            out |= extract_json_pointers(v, new_ptr)
        return out

    # scalar
    out.add(base)
    return out
