from shieldcraft.services.artifacts.lineage import build_lineage
from shieldcraft.services.stability.stability import compute_run_signature


def test_lineage_hash():
    l = build_lineage("p","a","b")
    assert "lineage_hash" in l


def test_signature():
    sig = compute_run_signature({
        "items": [],
        "rollups": {},
        "lineage": {"product_id":"p","spec_hash":"a","items_hash":"b","lineage_hash":"c"},
        "evidence": {"hash":"zzz"}
    })
    assert isinstance(sig,str) and len(sig)>10
