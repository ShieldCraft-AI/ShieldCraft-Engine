import pytest
from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_build_fails_on_missing_test_refs(monkeypatch, tmp_path):
    gen = ChecklistGenerator()

    # Monkeypatch AST builder to create minimal AST with one item lacking test_refs
    def fake_extract_from_ast(ast):
        return [{"ptr": "/sections/1", "key": "task-1"}]

    monkeypatch.setattr(gen, "_extract_from_ast", fake_extract_from_ast)

    # Create a minimal spec
    spec = {"metadata": {"product_id": "x"}, "sections": []}

    with pytest.raises(RuntimeError) as exc:
        gen.build(spec)
    assert "missing_test_refs" in str(exc.value)
