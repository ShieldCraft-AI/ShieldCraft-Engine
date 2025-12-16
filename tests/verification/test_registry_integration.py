from shieldcraft.verification.registry import global_registry
from shieldcraft.verification.scopes import VerificationScope


def test_registry_returns_baseline_properties_by_scope():
    reg = global_registry()
    spec_props = reg.get_by_scope(VerificationScope.SPEC.value)
    assert any(p.id == "VP-01-SPEC-TRACEABLE" for p in spec_props)
    persona_props = reg.get_by_scope(VerificationScope.PERSONA.value)
    assert any(p.id == "VP-04-PERSONA-NON-AUTHORITY" for p in persona_props)
