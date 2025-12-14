import pytest
from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_missing_test_refs_halts_generation(monkeypatch):
    gen = ChecklistGenerator()

    def fake_extract_from_ast(ast):
        return [{"ptr": "/", "key": "t1", "text": "x", "value": None}]

    monkeypatch.setattr(gen, "_extract_from_ast", fake_extract_from_ast)

    spec = {"metadata": {"product_id": "p"}, "sections": []}

    with pytest.raises(RuntimeError) as exc:
        gen.build(spec, run_test_gate=True)
    assert "missing_test_refs" in str(exc.value)
