import json

from shieldcraft.persona import find_persona_files, resolve_persona_files


def test_find_and_resolve_order(tmp_path):
    # Create multiple persona files with different versions
    (tmp_path / "personas").mkdir()
    a = tmp_path / "persona.json"
    b = tmp_path / "personas" / "A.json"
    c = tmp_path / "personas" / "B.json"
    a.write_text(json.dumps({"name": "root", "persona_version": "v1", "version": "1.2"}))
    b.write_text(json.dumps({"name": "a", "persona_version": "v1", "version": "1.10"}))
    c.write_text(json.dumps({"name": "b", "persona_version": "v1", "version": "1.2"}))

    paths = find_persona_files(str(tmp_path))
    # Deterministic discovery should contain all three
    assert set(paths) == {str(a), str(b), str(c)}

    chosen = resolve_persona_files(paths)
    # b has highest version 1.10 > 1.2
    assert chosen.endswith("/personas/A.json")


def test_resolution_tiebreaker(tmp_path):
    # Same version -> lexicographically smallest path wins
    (tmp_path / "personas").mkdir()
    p1 = tmp_path / "personas" / "x.json"
    p2 = tmp_path / "personas" / "y.json"
    p1.write_text(json.dumps({"name": "x", "persona_version": "v1", "version": "1.0"}))
    p2.write_text(json.dumps({"name": "y", "persona_version": "v1", "version": "1.0"}))

    paths = find_persona_files(str(tmp_path))
    chosen = resolve_persona_files(paths)
    assert chosen.endswith("/personas/x.json")
