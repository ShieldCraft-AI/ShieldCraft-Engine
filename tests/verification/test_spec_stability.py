from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_reordering_is_stable():
    gen = ChecklistGenerator()
    # sections as list to allow reorder mutation
    spec = {"sections": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}

    # Build baseline
    base = gen.build(spec, dry_run=True, run_fuzz=True, run_test_gate=False)
    base_items = base.get("items") or base.get("checklist", {}).get("items", [])

    # Create reordered spec and ensure checklist shape unchanged
    reordered = {"sections": list(reversed(spec["sections"]))}
    r = gen.build(reordered, dry_run=True, run_fuzz=True, run_test_gate=False)
    r_items = r.get("items") or r.get("checklist", {}).get("items", [])

    assert len(base_items) == len(r_items)
    assert {it.get("ptr") for it in base_items} == {it.get("ptr") for it in r_items}
