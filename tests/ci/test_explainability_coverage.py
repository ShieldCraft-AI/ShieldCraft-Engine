def test_explainability_coverage_in_checklist():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder

    spec = {"metadata": {"product_id": "ptest"}}
    ast = ASTBuilder().build(spec)
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True)
    items = chk.get('items', [])
    for it in items:
        meta = it.get('meta', {})
        if meta.get('synthesized_default') or meta.get('source') in ('coerced', 'derived', 'inferred', 'default'):
            assert 'source' in meta and meta.get('source')
            assert 'justification' in meta and meta.get('justification')
        # For coercions ensure original_value is preserved
        if meta.get('source') == 'coerced':
            assert 'original_value' in meta
