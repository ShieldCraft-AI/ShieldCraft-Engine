import pytest
from shieldcraft.verification.properties import VerificationProperty


def test_verification_property_immutable():
    p = VerificationProperty(id="VP-01", description="Test", scope="preflight", severity="low", deterministic=True)
    assert p.id == "VP-01"
    with pytest.raises(Exception):
        # frozen dataclass should prevent attribute assignment
        p.id = "x"
