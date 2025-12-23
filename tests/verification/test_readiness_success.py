from shieldcraft.verification.readiness_evaluator import evaluate_readiness


def test_readiness_success(monkeypatch):
    # Monkeypatch gates to succeed
    # Patch the functions used internally by the evaluator
    monkeypatch.setattr(
        "shieldcraft.verification.readiness_evaluator.enforce_spec_fuzz_stability",
        lambda s,
        g,
        max_variants=3: None)
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.enforce_tests_attached", lambda items: None)
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.enforce_persona_veto", lambda engine: None)
    # replay to match
    monkeypatch.setattr(
        "shieldcraft.verification.readiness_evaluator.replay_and_compare",
        lambda engine,
        rec: {
            "match": True})

    class DummyEngine:
        pass

    engine = DummyEngine()

    class DummyGen:
        def build(self, s, **kwargs):
            return {"items": []}

    engine.checklist_gen = DummyGen()
    spec = {"metadata": {"product_id": "p", "version": "1.0"}}
    checklist = {"items": [], "_determinism": {"spec": spec, "checklist": {}, "seeds": {}}}

    res = evaluate_readiness(engine, spec, checklist)
    assert res.get("ok") is True
