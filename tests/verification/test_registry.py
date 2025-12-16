import pytest
from shieldcraft.verification.registry import global_registry
from shieldcraft.verification.properties import VerificationProperty


def test_register_and_get_by_scope():
    reg = global_registry()
    # Backup state
    backup = dict(reg._by_id)
    try:
        # Clear for test
        reg._by_id.clear()
        p1 = VerificationProperty(id="VP-01", description="d", scope="preflight", severity="low")
        p2 = VerificationProperty(id="VP-02", description="d2", scope=["preflight", "snapshot"], severity="medium")
        reg.register(p1)
        reg.register(p2)
        all_props = reg.get_all()
        assert len(all_props) == 2
        pre = reg.get_by_scope("preflight")
        assert len(pre) == 2
        snap = reg.get_by_scope("snapshot")
        assert len(snap) == 1
        with pytest.raises(ValueError):
            reg.register(p1)
    finally:
        # Restore
        reg._by_id.clear()
        reg._by_id.update(backup)
