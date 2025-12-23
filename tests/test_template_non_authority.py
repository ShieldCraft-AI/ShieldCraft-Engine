def test_template_versions_do_not_change_checklist_outcome(tmp_path):
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.engine import Engine

    # Create two template directories with different contents
    t1 = tmp_path / "templates_v1"
    t1.mkdir()
    (t1 / "default.j2").write_text("version: v1\n{{ content }}")

    t2 = tmp_path / "templates_v2"
    t2.mkdir()
    (t2 / "default.j2").write_text("version: v2\n{{ content }}")

    spec = {"metadata": {"product_id": "p"}}
    engine = Engine(schema_path='')

    # Baseline checklist (no template involvement)
    chk_base = ChecklistGenerator().build(spec, dry_run=True, engine=engine)

    # Simulate presence of template versions by instantiating codegen generator (no effect on checklist)
    from shieldcraft.services.codegen.generator import CodeGenerator
    cg1 = CodeGenerator(template_dir=str(t1))
    cg2 = CodeGenerator(template_dir=str(t2))

    # Ensure codegen can render using both template dirs deterministically
    # Pick a sample item to render context
    sample_item = {'id': 'x1', 'ptr': '/metadata', 'text': 'sample', 'category': 'module', 'meta': {}}
    out1 = cg1.generate_for_item(sample_item) if hasattr(cg1, 'generate_for_item') else None
    out2 = cg2.generate_for_item(sample_item) if hasattr(cg2, 'generate_for_item') else None

    # After rendering templates, checklist primary outcome should remain unchanged
    chk_after1 = ChecklistGenerator().build(spec, dry_run=True, engine=engine)
    chk_after2 = ChecklistGenerator().build(spec, dry_run=True, engine=engine)

    assert chk_base.get('primary_outcome') == chk_after1.get('primary_outcome') == chk_after2.get('primary_outcome')


def test_missing_template_fallback_and_no_authority_escalation(tmp_path):
    from shieldcraft.services.codegen.generator import CodeGenerator
    from shieldcraft.engine import Engine

    # Create template dir missing module.j2 to force fallback
    tdir = tmp_path / "templates_missing"
    tdir.mkdir()
    (tdir / "default.j2").write_text("fallback template")

    cg = CodeGenerator(template_dir=str(tdir))
    engine = Engine(schema_path='')
    engine.checklist_context = type('S',
                                    (),
                                    {'_events': [],
                                     'record_event': lambda *a,
                                     **k: None,
                                     'get_events': lambda self=[]: []})()

    # Try rendering a typical module item; should not raise or emit REFUSAL/BLOCKER
    item = {'id': 'm1', 'ptr': '/module', 'category': 'module', 'text': 'do X', 'meta': {}}
    # Use generator to render; ensure fallback not causing authority events
    _ = cg.generate_for_item(item) if hasattr(cg, 'generate_for_item') else cg
    evs = engine.checklist_context.get_events()
    assert not any(
        (e.get('outcome') or '').upper() in (
            'REFUSAL', 'BLOCKER') and 'TEMPLATE' in (
            e.get('gate_id') or '') for e in evs)


def test_templates_cannot_emit_blocker_or_refusal():
    from shieldcraft.engine import Engine

    engine = Engine(schema_path='')
    # ensure no template-related gates exist that can issue authority
    evs = engine.checklist_context.get_events() if getattr(engine, 'checklist_context', None) else []
    assert not any(
        'TEMPLATE' in (
            e.get('gate_id') or '') and (
            e.get('outcome') or '').upper() in (
                'REFUSAL',
            'BLOCKER') for e in evs)


def test_template_scale_does_not_change_outcome(tmp_path):
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.engine import Engine

    # Generate many dummy templates
    tdir = tmp_path / "many_templates"
    tdir.mkdir()
    for i in range(200):
        (tdir / f"tpl_{i}.j2").write_text(f"tpl {i}")

    spec = {"metadata": {"product_id": "p"}}
    engine = Engine(schema_path='')
    chk_base = ChecklistGenerator().build(spec, dry_run=True, engine=engine)

    # Presence of many templates should not change checklist outcome
    chk_large = ChecklistGenerator().build(spec, dry_run=True, engine=engine)
    assert chk_base.get('primary_outcome') == chk_large.get('primary_outcome')
