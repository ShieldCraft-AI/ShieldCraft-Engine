def test_duplicate_redundant_sections_do_not_increase_synthesis():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.engine import Engine

    # Base spec (missing agents -> synthesized default expected once)
    base = {"metadata": {"product_id": "p"}}

    # Redundant spec: same base plus repeated filler sections
    redundant = {"metadata": {"product_id": "p"}, "filler": [{"x": i} for i in range(5)]}

    engine = Engine(schema_path='')
    chk_base = ChecklistGenerator().build(base, dry_run=True, engine=engine)
    chk_red = ChecklistGenerator().build(redundant, dry_run=True, engine=engine)

    items_base = chk_base.get('items', [])
    items_red = chk_red.get('items', [])

    synth_base = [it for it in items_base if (it.get('meta') or {}).get('synthesized_default')]
    synth_red = [it for it in items_red if (it.get('meta') or {}).get('synthesized_default')]

    # Number of synthesized items should be equal (no amplification)
    assert len(synth_base) == len(synth_red)
    # Primary outcomes equal
    assert chk_base.get('primary_outcome') == chk_red.get('primary_outcome')


def test_over_specification_extra_metadata_no_outcome_change():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.engine import Engine

    minimal = {"metadata": {"product_id": "x"}, "pipeline": {"states": ["ingest_spec"]}}
    detailed = dict(minimal)
    # Add extra non-conflicting metadata
    detailed["metadata"]["extra"] = {"notes": "verbose", "author": "tester"}

    engine = Engine(schema_path='')
    chk_min = ChecklistGenerator().build(minimal, dry_run=True, engine=engine)
    chk_det = ChecklistGenerator().build(detailed, dry_run=True, engine=engine)

    assert chk_min.get('primary_outcome') == chk_det.get('primary_outcome')
    # No escalation of severity counts
    sev_min = sorted([it['severity'] for it in chk_min.get('items', [])])
    sev_det = sorted([it['severity'] for it in chk_det.get('items', [])])
    assert sev_min == sev_det


def test_conflicting_explicit_instructions_surface_diagnostic():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.engine import Engine

    # Conflicting invariants: one requires agents exist, another requires none
    spec = {"metadata": {"product_id": "p"}, "sections": [
        {"name": "a", "must": "count(/agents) > 0"}, {"name": "b", "must": "count(/agents) == 0"}], "agents": []}

    engine = Engine(schema_path='')
    chk = ChecklistGenerator().build(spec, dry_run=True, engine=engine)
    items = chk.get('items', [])

    # Look for invariant diagnostics or DIAGNOSTIC/BLOCKER items referencing invariants
    found = any(
        'INVARIANT' in (
            it.get('text') or '') or (
            it.get('meta') or {}).get('invariant_results') for it in items)
    assert found, 'Conflicting invariants must be surfaced as diagnostics'


def test_scale_invariance_primary_outcome_stable():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.engine import Engine

    base = {"metadata": {"product_id": "p"}, "pipeline": {"states": ["ingest_spec"]}}

    # Create large spec by adding many unrelated filler sections
    large = dict(base)
    large["extras"] = [{"name": f"f{i}", "note": "irrelevant"} for i in range(200)]

    engine = Engine(schema_path='')
    chk_base = ChecklistGenerator().build(base, dry_run=True, engine=engine)
    chk_large = ChecklistGenerator().build(large, dry_run=True, engine=engine)

    assert chk_base.get('primary_outcome') == chk_large.get('primary_outcome')

    # Ensure deterministic ordering: compare list of item ids for core items
    base_ids = [it.get('id') for it in chk_base.get('items', [])]
    large_ids = [it.get('id') for it in chk_large.get('items', []) if (it.get('ptr') or '').startswith('/')]
    # Core id sets should be subset/equal for invariance
    assert set(base_ids).issubset(set(large_ids))
