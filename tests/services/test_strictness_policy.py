

def test_policy_mapping_and_serialization(monkeypatch):
    from shieldcraft.services.spec.strictness_policy import SemanticStrictnessPolicy

    monkeypatch.delenv("SEMANTIC_STRICTNESS_LEVEL_1", raising=False)
    monkeypatch.delenv("SEMANTIC_STRICTNESS_LEVEL_2", raising=False)
    monkeypatch.delenv("SEMANTIC_STRICTNESS_DISABLED", raising=False)
    p = SemanticStrictnessPolicy.from_env()
    # Level 1 is enabled by default unless explicitly disabled
    assert p.active_levels() == [1]
    assert len(p.enforced_rules()) >= 1

    monkeypatch.setenv("SEMANTIC_STRICTNESS_LEVEL_1", "1")
    p = SemanticStrictnessPolicy.from_env()
    assert p.active_levels() == [1]
    rules = p.enforced_rules()
    assert len(rules) == 1 and rules[0]["section"] == "sections"

    monkeypatch.setenv("SEMANTIC_STRICTNESS_LEVEL_2", "1")
    p = SemanticStrictnessPolicy.from_env()
    assert p.active_levels() == [1, 2]
    assert any(r["section"] == "invariants" for r in p.enforced_rules())

    d = p.to_dict()
    assert "active_levels" in d and "enforced_sections" in d
