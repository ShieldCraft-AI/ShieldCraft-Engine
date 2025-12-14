from shieldcraft.verification.registry import global_registry
from shieldcraft.verification.baseline import BASELINE_PROPERTIES


def test_baseline_properties_registered_and_deterministic():
    reg = global_registry()
    ids = {p.id for p in reg.get_all()}
    for bp in BASELINE_PROPERTIES:
        assert bp.id in ids
        assert bp.deterministic is True
        assert bp.scope is not None
        assert isinstance(bp.severity, str)
