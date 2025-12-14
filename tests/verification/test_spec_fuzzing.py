import pytest
from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_spec_contradiction_fails_fast(tmp_path, monkeypatch):
    gen = ChecklistGenerator()

    # Create spec with one section
    spec = {"metadata": {"product_id": "x"}, "sections": {"1": {"id": "s1"}}}

    # Monkeypatch fuzzer to produce a contradictory variant
    from shieldcraft.verification.spec_fuzzer import generate_mutations

    muts = generate_mutations(spec)
    # Ensure there is a contradiction mutation
    assert any(kind == "contradiction" for _, kind, _ in muts)

    with pytest.raises(RuntimeError) as exc:
        gen.build(spec, run_fuzz=True)
    assert any(k in str(exc.value) for k in ("SPEC_CONTRADICTORY", "SPEC_INCOMPLETE", "SPEC_DRIFT"))
