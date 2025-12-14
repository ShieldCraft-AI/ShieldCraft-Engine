import pytest
from shieldcraft.services.validator import validate_spec_instructions


def test_missing_invariants_fails():
    spec = {
        "metadata": {"product_id": "x"},
        "instructions": [
            {"id": "step.1", "type": "verification", "description": "v"}
        ]
    }

    with pytest.raises(ValueError, match="missing invariants"):
        validate_spec_instructions(spec)


def test_ambient_state_fails():
    spec = {
        "metadata": {"product_id": "x"},
        "invariants": ["No ambient state"],
        "instructions": [
            {"id": "step.1", "type": "construction", "timestamp": "2025-12-14T00:00:00Z"}
        ]
    }

    with pytest.raises(ValueError, match="ambient state"):
        validate_spec_instructions(spec)


def test_validation_deterministic_on_repeat():
    """Repeated validation on identical invalid spec yields identical error objects."""
    from shieldcraft.services.validator import ValidationError

    spec = {
        "metadata": {"product_id": "x"},
        "invariants": ["no ambient"],
        "instructions": [{"id": "i1", "type": "construction", "timestamp": "now"}],
    }

    err1 = None
    err2 = None
    try:
        validate_spec_instructions(spec)
    except ValidationError as e:
        err1 = e.to_dict()

    try:
        validate_spec_instructions(spec)
    except ValidationError as e:
        err2 = e.to_dict()

    assert err1 == err2


def test_valid_spec_passes():
    spec = {
        "metadata": {"product_id": "x"},
        "invariants": ["No ambient state"],
        "instructions": [
            {"id": "step.1", "type": "verification"},
            {"id": "step.2", "type": "construction", "depends_on_invariants": True}
        ]
    }

    # Should not raise
    validate_spec_instructions(spec)
