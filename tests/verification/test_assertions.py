import pytest
from shieldcraft.verification.properties import VerificationProperty
from shieldcraft.verification.assertions import assert_verification_properties


def test_assertion_raises_on_invalid_severity():
    p = VerificationProperty(id="VP-01", description="d", scope="preflight", severity="invalid")
    with pytest.raises(RuntimeError):
        assert_verification_properties([p])


def test_assertion_ok_for_valid_property():
    p = VerificationProperty(id="VP-02", description="d2", scope="preflight", severity="low")
    # should not raise
    assert_verification_properties([p])
