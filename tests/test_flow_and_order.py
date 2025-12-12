from shieldcraft.services.checklist.flow import compute_flow
from shieldcraft.services.checklist.order import ordering_constraints

def test_compute_flow():
    spec = {"metadata":{}, "architecture":{}, "agents":{}, "api":{}}
    f = compute_flow(spec)
    assert ("metadata","architecture") in f

def test_ordering_constraints():
    raw = [
        {"ptr":"/metadata/x","text":"a","value":1},
        {"ptr":"/architecture/y","text":"b","value":2},
    ]
    out = ordering_constraints(raw)
    assert any("/_order" in i["ptr"] for i in out)
