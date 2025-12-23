from shieldcraft.verification.readiness_evaluator import evaluate_readiness


def test_readiness_summary_on_success(monkeypatch):
    # All gates succeed -> grade 'A' and zero blocking
    monkeypatch.setattr(
        "shieldcraft.verification.readiness_evaluator.enforce_spec_fuzz_stability",
        lambda s,
        g,
        max_variants=3: None)
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.enforce_tests_attached", lambda items: None)
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.enforce_persona_veto", lambda engine: None)
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
    rs = res.get("readiness_summary")
    assert rs is not None
    assert rs.get("blocking_count") == 0
    assert rs.get("grade") == "A"


def test_readiness_summary_blocking_failure(monkeypatch):
    # determinism_replay fails (blocking gate) -> grade 'F' and blocking_count >=1
    monkeypatch.setattr(
        "shieldcraft.verification.readiness_evaluator.enforce_spec_fuzz_stability",
        lambda s,
        g,
        max_variants=3: None)
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.enforce_tests_attached", lambda items: None)
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.enforce_persona_veto", lambda engine: None)
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.replay_and_compare",
                        lambda engine, rec: {"match": False, "explanation": "mismatch"})

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
    rs = res.get("readiness_summary")
    assert rs is not None
    assert rs.get("blocking_count") >= 1
    assert rs.get("grade") == "F"
    assert res.get("ok") is False
