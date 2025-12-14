import pytest
from shieldcraft.services.validator import (
    validate_spec_instructions,
    ValidationError,
    VALIDATION_ERROR_CODES,
)


def test_missing_instructions_fails():
    spec = {"metadata": {"product_id": "x"}, "invariants": ["inv.1"]}
    with pytest.raises(ValidationError) as e:
        validate_spec_instructions(spec)
    assert e.value.code in VALIDATION_ERROR_CODES


def test_instruction_not_object():
    spec = {"metadata": {"product_id": "x"}, "invariants": ["inv.1"], "instructions": ["not_an_obj"]}
    with pytest.raises(ValidationError) as e:
        validate_spec_instructions(spec)
    assert e.value.code in VALIDATION_ERROR_CODES


def test_instruction_missing_fields():
    spec = {"metadata": {"product_id": "x"}, "invariants": ["inv.1"], "instructions": [{}]}
    with pytest.raises(ValidationError) as e:
        validate_spec_instructions(spec)
    assert e.value.code in VALIDATION_ERROR_CODES


def test_duplicate_instruction_id():
    spec = {
        "metadata": {"product_id": "x"},
        "invariants": ["inv.1"],
        "instructions": [{"id": "i1", "type": "t"}, {"id": "i1", "type": "t"}],
    }
    with pytest.raises(ValidationError) as e:
        validate_spec_instructions(spec)
    assert e.value.code in VALIDATION_ERROR_CODES


def test_invariants_not_sorted_for_dicts():
    spec = {
        "metadata": {"product_id": "x"},
        "invariants": [{"id": "b"}, {"id": "a"}],
        "instructions": [{"id": "i1", "type": "t"}],
    }
    with pytest.raises(ValidationError) as e:
        validate_spec_instructions(spec)
    assert e.value.code == "invariants_not_sorted"


def test_spec_not_dict_error():
    with pytest.raises(ValidationError) as e:
        validate_spec_instructions("notadict")
    assert e.value.code == "spec_not_dict"
