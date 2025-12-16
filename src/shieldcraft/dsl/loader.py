"""
Canonical DSL loader for ShieldCraft Engine.
Exclusively loads canonical JSON specs.
"""
import json
import pathlib
import logging
from shieldcraft.dsl.canonical_loader import load_canonical_spec
from shieldcraft.services.spec.ingestion import ingest_spec

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
    data = ingest_spec(path)

    # Ensure loader always returns a dict; ingestion guarantees this envelope
    if not isinstance(data, dict):
        # As a defensive fallback, wrap into the canonical envelope
        data = {"metadata": {"source_format": "unknown", "normalized": True}, "raw_input": data}
    
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
            # If this spec was produced by the ingestion normalization
            # (metadata.normalized == True) it is not a true canonical
            # file on disk; treat it as a legacy/normalized payload and
            # do not attempt to re-load the file as canonical JSON which
            # could bypass schema checks for missing required fields.
            if data.get('metadata', {}).get('normalized'):
                # Return the normalized DSL-shaped payload for downstream
                # schema validation to run deterministically.
                return data
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
    
    # Detect canonical vs legacy and prefer dsl_version/spec_format mapping
    if dsl_version == _DSL_VERSION_REQUIRED:
        return load_canonical_spec(path)
    # Fallback to legacy detection (legacy payload may still include explicit signals)
    if isinstance(data, dict) and ('canonical' in data or 'canonical_spec_hash' in data.get('metadata', {})):
        return load_canonical_spec(path)
    # Default: legacy spec, deprecated
    logger.warning(f"DEPRECATION: old DSL format in use at {path}; migrate to canonical JSON.")
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
