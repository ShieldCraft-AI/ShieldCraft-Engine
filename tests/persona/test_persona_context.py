import json

from shieldcraft.persona import PersonaContext


def test_persona_context_serialization_stable():
    ctx = PersonaContext(name="Fiona", role="cofounder", display_name="Fiona",
                         scope=["engineering", "design"], allowed_actions=["advise"], constraints={})
    s1 = ctx.to_canonical_json()
    s2 = ctx.to_canonical_json()
    assert s1 == s2
    # Keys should be deterministically ordered in canonical form
    assert '"name"' in s1 and '"scope"' in s1


def test_persona_conflict_detection(tmp_path):
    (tmp_path / "personas").mkdir()
    p1 = tmp_path / "personas" / "a.json"
    p2 = tmp_path / "personas" / "b.json"
    p1.write_text(json.dumps({"name": "X", "persona_version": "v1", "scope": ["a"]}))
    p2.write_text(json.dumps({"name": "X", "persona_version": "v1", "scope": ["b"]}))

    from shieldcraft.persona import find_persona_files, detect_conflicts
    paths = find_persona_files(str(tmp_path))
    errs = detect_conflicts(paths)
    assert len(errs) >= 1
    codes = {e["code"] for e in errs}
    assert "persona_conflict_incompatible_scope" in codes
