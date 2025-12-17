def test_tier_enforcement_emits_items_and_records_events():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.engine import Engine

    # Spec deliberately missing Tier A 'agents' and Tier B 'generation_mappings'
    spec = {
        "metadata": {"product_id": "testprod"},
        "pipeline": {"states": ["ingest_spec", "done"]}
    }

    ast = ASTBuilder().build(spec)
    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []

        def record_event(self, *args, **kwargs):
            self._events.append((args, kwargs))

        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()

    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True, run_fuzz=False, engine=engine)
    items = chk.get('items', [])

    # Find synthesized items
    synth_items = [it for it in items if (it.get('meta') or {}).get('synthesized_default')]
    ptrs = {it.get('ptr') for it in synth_items}
    # At least one Tier A synthesized item must be present (agents/evidence_bundle/etc.)
    assert any((it.get('meta') or {}).get('tier') == 'A' for it in synth_items)
    # Generation mappings is Tier B and should be synthesized
    assert '/generation_mappings' in ptrs

    # Check recorded events include both missing and synthesized events
    recs = engine.checklist_context._events
    assert any('G_TIER_A_MISSING_AGENTS' in a[0] for a in recs)
    assert any('G_SYNTHESIZED_DEFAULT_AGENTS' in a[0] for a in recs)
    assert any('G_TIER_B_MISSING_GENERATION_MAPPINGS' in a[0] for a in recs)
    assert any('G_SYNTHESIZED_DEFAULT_GENERATION_MAPPINGS' in a[0] for a in recs)
