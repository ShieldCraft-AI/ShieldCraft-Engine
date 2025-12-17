def test_all_items_have_explainability_when_inferred_or_coerced():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder

    spec = {"metadata": {"product_id": "testprod"}, "pipeline": {"states": ["ingest_spec"]}}
    ast = ASTBuilder().build(spec)
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True)
    items = chk.get('items', [])
    for it in items:
        meta = it.get('meta', {})
        # If item was synthesized, coerced, inferred or derived ensure explainability fields exist
        if meta.get('synthesized_default') or meta.get('source') in ('coerced', 'derived', 'inferred', 'default'):
            assert meta.get('source') in ('default', 'explicit', 'derived', 'coerced', 'inferred')
            assert meta.get('justification')
            assert meta.get('inference_type') in ('none', 'safe_default', 'heuristic', 'structural', 'fallback')
