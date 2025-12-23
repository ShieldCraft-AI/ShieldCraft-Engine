from shieldcraft.services.spec.normalization import build_minimal_dsl_skeleton
from shieldcraft.engine import Engine
from shieldcraft.services.validator import ValidationError


def test_authoring_readiness_progression(monkeypatch):
    """Simulate an author incrementally filling the DSL skeleton and assert
    validation errors evolve predictably as sections are populated.
    """
    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    monkeypatch.delenv("SEMANTIC_STRICTNESS_DISABLED", raising=False)
    monkeypatch.setenv("SEMANTIC_STRICTNESS_LEVEL_2", "1")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative",
                        lambda root: {"ok": True, "sha256": "abc"})

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Start with minimal normalized skeleton
    spec = build_minimal_dsl_skeleton("", source_format="text")

    # Default Level 1 enforces sections
    try:
        engine.run_self_host(spec, dry_run=True)
        assert False, "Expected sections_empty"
    except ValidationError as e:
        assert e.code == "sections_empty"
        assert "rationale" in (e.to_dict().get("details") or {})

    # Author adds sections (satisfy Level 1)
    spec["sections"] = [{"id": "s1"}]

    # Now Level 2 enforces invariants
    try:
        engine.run_self_host(spec, dry_run=True)
        assert False, "Expected invariants_empty under Level 2"
    except ValidationError as e:
        assert e.code == "invariants_empty"
        assert "expected" in (e.to_dict().get("details") or {})

    # Author adds invariants
    spec["invariants"] = ["i1"]

    # Now Level 2 should enforce model
    try:
        engine.run_self_host(spec, dry_run=True)
        assert False, "Expected model_empty under Level 2"
    except ValidationError as e:
        assert e.code == "model_empty"

    # Author adds model
    spec["model"] = {"version": "1.0"}

    # Now minimal set satisfied; run should proceed (may still raise other semantic readiness issues)
    res = engine.run_self_host(spec, dry_run=True)
    assert isinstance(res, dict)
