from shieldcraft.services.checklist.grouping import group_items
from shieldcraft.services.checklist.rollup import build_rollups
from shieldcraft.services.checklist.evidence import build_evidence_bundle


def test_grouping_basic():
    items=[{"ptr":"/a","text":"x","classification":"meta","severity":"high","order_rank":(1,),"id":"test1"}]
    g=group_items(items)
    # Updated: hierarchical grouping now includes section
    assert "meta.high.default" in g


def test_rollup_basic():
    items=[{"ptr":"/a","text":"SPEC MISSING: x","classification":"meta","severity":"critical","id":"test1"}]
    # Updated: hierarchical grouping now includes section
    grouped={"meta.critical.default":{"items":items,"order_key":("meta",0,"default")}}
    r=build_rollups(grouped)
    assert r["total"]==1
    assert r["by_severity"]["critical"]==1
    assert r["missing"]


def test_evidence_bundle():
    b = build_evidence_bundle("p", [], {})
    assert "hash" in b
