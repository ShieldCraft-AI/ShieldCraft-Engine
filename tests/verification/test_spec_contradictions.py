import pytest
from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_spec_contradiction_detected():
    gen = ChecklistGenerator()
    spec = {"metadata": {"product_id": "x"}, "sections": {"1": {"id": "s1"}}}

    # Directly craft a contradictory spec mutation and assert gate would flag it
    mutated = {"metadata": {"product_id": "x"}, "sections": {"1": {"id": "s1"}, "conflict_1": {"id": "s1", "description": "conflict"}}}

    from shieldcraft.verification.spec_fuzzer import classify_mutation
    cls = classify_mutation(spec, mutated, "contradiction")
    assert cls == "SPEC_CONTRADICTORY"
