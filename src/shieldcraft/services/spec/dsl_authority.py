"""
DSL Authority Guard for ShieldCraft Engine.

Enforces canonical DSL contract and prevents drift.
"""
import pathlib


_CANONICAL_DSL_VERSION = "canonical_v1_frozen"
_CANONICAL_SCHEMA_PATH = "spec/schemas/se_dsl_v1.schema.json"


def verify_canonical_dsl(spec, schema_path=None):
    """
    Verify spec uses canonical DSL v1 frozen.

    Args:
        spec: Spec dict or SpecModel
        schema_path: Path to schema (optional, defaults to canonical)

    Returns:
        bool: True if valid

    Raises:
        ValueError: If DSL version mismatch or schema path incorrect
    """
    # Extract spec dict if SpecModel
    from shieldcraft.services.spec.model import SpecModel
    if isinstance(spec, SpecModel):
        spec_dict = spec.raw
    elif isinstance(spec, dict):
        spec_dict = spec
    else:
        raise TypeError(f"spec must be dict or SpecModel, got {type(spec)}")

    # Check DSL version
    dsl_version = spec_dict.get('dsl_version')
    if dsl_version != _CANONICAL_DSL_VERSION:
        raise ValueError(
            f"DSL authority violation: expected dsl_version='{_CANONICAL_DSL_VERSION}', "
            f"got '{dsl_version}'"
        )

    # Check schema path if provided
    if schema_path:
        provided_path = pathlib.Path(schema_path)

        # Normalize and compare
        if not str(provided_path).endswith('se_dsl_v1.schema.json'):
            raise ValueError(
                f"DSL authority violation: schema path must be '{_CANONICAL_SCHEMA_PATH}', "
                f"got '{schema_path}'"
            )

    return True


def get_canonical_dsl_version():
    """Return the canonical DSL version string."""
    return _CANONICAL_DSL_VERSION


def get_canonical_schema_path():
    """Return the canonical schema path."""
    return _CANONICAL_SCHEMA_PATH
