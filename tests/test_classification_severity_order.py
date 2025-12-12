from shieldcraft.services.checklist.classify import classify_item
from shieldcraft.services.checklist.severity import compute_severity
from shieldcraft.services.checklist.order import assign_order_rank
from shieldcraft.services.checklist.idgen import synthesize_id

def test_classify():
    item = {"ptr":"/metadata/x","text":"T"}
    assert classify_item(item) == "metadata"

def test_severity_missing():
    item = {"ptr":"/x","text":"SPEC MISSING: y","classification":"general"}
    assert compute_severity(item) == "critical"

def test_order_rank():
    item = {"ptr":"/a","text":"t","severity":"high","classification":"api"}
    r = assign_order_rank(item)
    assert r[0] == 1

def test_idgen():
    item = {"ptr":"/a","text":"x"}
    assert len(synthesize_id(item)) == 12
