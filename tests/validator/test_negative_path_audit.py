import json
import pytest
from shieldcraft.services.validator import (
    validate_instruction_block,
    ValidationError,
    VALIDATION_ERROR_CODES,
)


def _assert_code_for_spec(spec, expected_code):
    with pytest.raises(ValidationError) as e:
        validate_instruction_block(spec)
    err = e.value.to_dict()
    assert err["code"] == expected_code
    assert isinstance(err["message"], str) and err["message"]
    # location may be None or string


def test_negative_path_enumeration():
    # spec_not_dict
    with pytest.raises(ValidationError) as e:
        validate_instruction_block("notadict")
    assert e.value.code == "spec_not_dict"

    # missing_invariants
    spec = {"metadata": {"product_id": "x"}, "instructions": [{"id": "i1", "type": "t"}]}
    _assert_code_for_spec(spec, "missing_invariants")

    # invariants_not_sorted (dicts)
    spec = {"metadata": {"product_id": "x"}, "invariants": [{"id": "b"}, {"id": "a"}], "instructions": [{"id":"i1","type":"t"}]}
    _assert_code_for_spec(spec, "invariants_not_sorted")

    # missing_instructions
    spec = {"metadata": {"product_id": "x"}, "invariants": ["inv.1"]}
    _assert_code_for_spec(spec, "missing_instructions")

    # instruction_not_object
    spec = {"metadata": {"product_id": "x"}, "invariants": ["inv.1"], "instructions": ["not_an_obj"]}
    _assert_code_for_spec(spec, "instruction_not_object")

    # instruction_missing_fields
    spec = {"metadata": {"product_id": "x"}, "invariants": ["inv.1"], "instructions": [{}]}
    _assert_code_for_spec(spec, "instruction_missing_fields")

    # duplicate_instruction_id
    spec = {"metadata": {"product_id": "x"}, "invariants": ["inv.1"], "instructions": [{"id":"i","type":"t"},{"id":"i","type":"t"}]}
    _assert_code_for_spec(spec, "duplicate_instruction_id")

    # ambient_state
    spec = {"metadata": {"product_id": "x"}, "invariants": ["inv.1"], "instructions": [{"id":"i","type":"t","timestamp":"now"}]}
    _assert_code_for_spec(spec, "ambient_state")
