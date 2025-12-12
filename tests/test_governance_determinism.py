from shieldcraft.services.governance.determinism import DeterminismEngine


def test_canonical_json():
    det = DeterminismEngine()
    obj = {"b": 2, "a": 1}
    assert det.canonicalize(obj) == '{"a":1,"b":2}'
