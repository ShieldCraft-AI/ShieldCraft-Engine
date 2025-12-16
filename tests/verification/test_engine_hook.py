from types import SimpleNamespace
from shieldcraft.engine import Engine


def test_engine_preflight_invokes_verification(monkeypatch, tmp_path):
    called = SimpleNamespace(flag=False)

    def fake_assert(props):
        called.flag = True

    import shieldcraft.verification.assertions as va
    monkeypatch.setattr(va, "assert_verification_properties", fake_assert)

    eng = Engine(schema_path=str(tmp_path))
    # call preflight on a minimal valid skeleton to ensure verification hook runs
    eng.preflight({"sections": [{"id": "min"}], "model": {}})
    assert called.flag is True
