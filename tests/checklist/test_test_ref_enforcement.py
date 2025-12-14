import pytest
from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_build_fails_on_missing_test_refs(monkeypatch, tmp_path):
    gen = ChecklistGenerator()

    # Monkeypatch AST builder to create minimal AST with one item lacking test_refs
    def fake_extract_from_ast(ast):
        # Use root pointer which will be present in minimal AST lineage
        # Provide minimal fields expected by downstream processing
        return [{"ptr": "/", "key": "task-1", "text": "Implement value at /", "value": None}]

    monkeypatch.setattr(gen, "_extract_from_ast", fake_extract_from_ast)

    # Create a minimal spec
    spec = {"metadata": {"product_id": "x"}, "sections": []}

    result = gen.build(spec)
    # Generation should report contract violations for missing test refs
    assert result is not None
    assert result.get("valid") is False
    contract_violations = result.get("preflight", {}).get("contract_violations", [])
    assert any("missing_test_refs" in v for v in contract_violations)
