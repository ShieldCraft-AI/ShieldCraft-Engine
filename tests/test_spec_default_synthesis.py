def test_synthesize_missing_spec_fields_detects_and_injects_defaults():
    from shieldcraft.services.spec.defaults import synthesize_missing_spec_fields

    spec = {"metadata": {"product_id": "x"}}
    new_spec, synthesized = synthesize_missing_spec_fields(spec)
    assert "agents" in synthesized
    assert "generation_mappings" in synthesized
    assert new_spec.get("agents") == []
    assert isinstance(new_spec.get("generation_mappings"), dict)


def test_tier_a_synthesized_default_emits_blocker_and_has_provenance():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.engine import Engine

    spec = {"metadata": {"product_id": "x"}}  # missing agents -> Tier A
    ast = ASTBuilder().build(spec)
    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []
        def record_event(self, gate_id, phase, outcome, message=None, evidence=None, **kwargs):
            self._events.append({'gate_id': gate_id, 'phase': phase, 'outcome': outcome, 'message': message, 'evidence': evidence})
        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True, engine=engine)
    # Ensure a BLOCKER event was recorded for synthesized agents
    evs = engine.checklist_context.get_events()
    assert any(e.get('gate_id') == 'G_SYNTHESIZED_DEFAULT_AGENTS' and e.get('outcome') == 'BLOCKER' for e in evs)
    # Ensure synthesized default provenance is present (either as an item or in spec metadata)
    items = chk.get('items', [])
    synths = [it for it in items if (it.get('meta') or {}).get('synthesized_default')]
    # Either an explicit synthesized item with a justification_ptr exists OR spec-level synthesized metadata records it
    has_item_prov = any(it.get('meta', {}).get('justification_ptr') == '/agents' and it.get('meta', {}).get('source') == 'default' for it in synths)
    # The generator records synthesized defaults as gate events if not visible in final items. Check for the recorded event evidence as an alternative
    has_event_prov = any(e.get('gate_id') == 'G_SYNTHESIZED_DEFAULT_AGENTS' and e.get('evidence', {}).get('section') == 'agents' for e in evs)
    assert has_item_prov or has_event_prov


def test_tier_b_synthesized_default_emits_diagnostic_and_has_provenance():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder

    spec = {"metadata": {"product_id": "x"}, "agents": []}  # missing determinism -> Tier B
    ast = ASTBuilder().build(spec)
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True)
    items = chk.get('items', [])
    synths = [it for it in items if (it.get('meta') or {}).get('synthesized_default')]
    assert any(it.get('meta', {}).get('justification_ptr') == '/determinism' and it.get('meta', {}).get('tier') == 'B' for it in synths)


def test_synthesized_defaults_do_not_change_upstream_shape_when_present():
    from shieldcraft.services.spec.defaults import synthesize_missing_spec_fields
    # If spec already has the key, synthesized list is empty
    spec = {"metadata": {"product_id": "x"}, "agents": [{"id": "a1"}], "generation_mappings": {"components": []}}
    new_spec, synthesized = synthesize_missing_spec_fields(spec)
    # Agents and generation_mappings should not be synthesized since present
    assert 'agents' not in synthesized
    assert 'generation_mappings' not in synthesized
    assert new_spec.get("agents") == spec.get("agents")
    assert new_spec.get("generation_mappings") == spec.get("generation_mappings")
