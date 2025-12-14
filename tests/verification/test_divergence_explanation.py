from shieldcraft.engine import Engine
from shieldcraft.verification.seed_manager import generate_seed
from shieldcraft.verification.replay_engine import replay_and_compare


def test_divergence_is_explained(monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = {"metadata": {"product_id": "p", "version": "1.0"}, "sections": {"core": {"description": "x"}}}

    # Baseline run
    res1 = engine.checklist_gen.build(spec, engine=engine)
    det = {"spec": spec, "ast": res1.get("items") and None, "checklist": res1, "seeds": {}
           }

    # Mutate seed and replay - expect divergence and explanation
    generate_seed(engine, "run", seed="cafebabe")
    r = replay_and_compare(engine, det)
    assert r.get("match") is False
    exp = r.get("explanation")
    assert exp and "diff_keys" in exp
