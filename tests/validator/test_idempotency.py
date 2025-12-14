from shieldcraft.services.validator import validate_instruction_block, ValidationError


def test_validation_idempotent_on_success():
    spec = {
        "metadata": {"product_id": "x"},
        "invariants": ["inv1"],
        "instructions": [{"id": "i1", "type": "t"}],
    }

    # Should not raise on successive runs
    validate_instruction_block(spec)
    validate_instruction_block(spec)


def test_validation_idempotent_on_failure():
    spec = {
        "metadata": {"product_id": "x"},
        "invariants": ["inv1"],
        "instructions": [{"id": "i1", "type": "t", "timestamp": "now"}],
    }

    err1 = None
    err2 = None
    try:
        validate_instruction_block(spec)
    except ValidationError as e:
        err1 = e.to_dict()

    try:
        validate_instruction_block(spec)
    except ValidationError as e:
        err2 = e.to_dict()

    assert err1 == err2
