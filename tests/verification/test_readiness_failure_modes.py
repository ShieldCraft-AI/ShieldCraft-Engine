from shieldcraft.verification.readiness_evaluator import evaluate_readiness


def test_readiness_fails_on_missing_tests(monkeypatch):
    # Let spec gate pass
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.enforce_spec_fuzz_stability", lambda s, g, max_variants=3: None)
    # Make tests attached raise
    def _fail(items):
        raise RuntimeError("missing_test_refs:[x]")
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.enforce_tests_attached", _fail)
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.enforce_persona_veto", lambda e: None)
    monkeypatch.setattr("shieldcraft.verification.readiness_evaluator.replay_and_compare", lambda engine, rec: {"match": True})

    class DummyEngine:
        pass

    engine = DummyEngine()
    spec = {"metadata": {"product_id": "p", "version": "1.0"}}
    checklist = {"items": []}

    res = evaluate_readiness(engine, spec, checklist)
    assert res.get("ok") is False
    assert "tests_attached" in res.get("results") and not res["results"]["tests_attached"]["ok"]
