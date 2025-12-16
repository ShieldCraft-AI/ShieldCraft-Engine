import json
import pathlib


def build_checklist_for(path):
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    spec = json.load(open(path))
    ast = ASTBuilder().build(spec)
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True, run_test_gate=False)
    return chk


def test_valid_demo_has_confidence_and_evidence():
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    spec_path = str(repo_root / "demos" / "valid.json")
    chk = build_checklist_for(spec_path)
    items = chk.get("items", [])
    assert len(items) > 0
    # Post-process via enrichment helpers to simulate emitted form
    from shieldcraft.services.guidance.checklist import enrich_with_confidence_and_evidence, ensure_item_fields
    enrich_with_confidence_and_evidence(items, json.load(open(spec_path)))
    ensure_item_fields(items)
    # At least one item should carry a confidence and evidence pointer
    assert any(it.get("confidence") in ("low", "medium", "high") for it in items)
    assert any(isinstance(it.get("evidence"), dict) and "source" in it.get("evidence") for it in items)


def test_prose_inference_on_inline_spec():
    # Inline prose spec to assert inference works without external files
    spec = {
        "metadata": {"product_id": "prose_test", "self_host": True},
        "sections": [{"name": "intro", "text": "This service must never expose keys and must refuse unsafe defaults."}]
    }
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    ast = ASTBuilder().build(spec)
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True, run_test_gate=False)
    items = chk.get("items", [])
    assert len(items) > 0
    from shieldcraft.services.guidance.checklist import enrich_with_confidence_and_evidence, ensure_item_fields
    enrich_with_confidence_and_evidence(items, spec)
    ensure_item_fields(items)
    assert any(it.get("inferred_from_prose") is True and it.get("confidence") == "low" for it in items)
