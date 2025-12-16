from shieldcraft.services.spec.conversion_state import ConversionState


def test_conversion_state_enum_locked():
    expected = {"ACCEPTED", "CONVERTIBLE", "STRUCTURED", "VALID", "READY", "INCOMPLETE"}
    actual = {m.name for m in ConversionState}
    assert actual == expected, "ConversionState enum must match frozen contract for SE v1"


def test_no_new_states_without_schema_bump():
    # This test enforces the contract at runtime; adding new names will fail this assertion.
    expected_order = ["ACCEPTED", "CONVERTIBLE", "STRUCTURED", "VALID", "READY", "INCOMPLETE"]
    assert [m.name for m in ConversionState] == expected_order
