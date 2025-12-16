from shieldcraft.engine import Engine
from shieldcraft.verification.seed_manager import generate_seed


def test_seed_changes_cause_marker_variation(monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}

    # Default run seed
    from shieldcraft.verification.seed_manager import generate_seed
    generate_seed(engine, "run")
    res1 = engine.checklist_gen.build(spec, engine=engine)
    items1 = sorted([i.get("meta", {}).get("determinism_marker") for i in res1.get("items", [])])

    # Force new seed
    generate_seed(engine, "run", seed="deadbeef")
    res2 = engine.checklist_gen.build(spec, engine=engine)
    items2 = sorted([i.get("meta", {}).get("determinism_marker") for i in res2.get("items", [])])

    assert items1 != items2
