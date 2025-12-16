from shieldcraft.verification.scopes import VerificationScope


def test_scopes_stability_and_uniqueness():
    names = [s.name for s in VerificationScope]
    assert len(names) == len(set(names))
    expected = {"SPEC", "CHECKLIST", "CODE", "TESTS", "PERSONA", "OUTPUT", "SYSTEM"}
    assert set(names) == expected
