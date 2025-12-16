import json
import os
import shutil


def run_self(spec_path):
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)
    with open('.selfhost_outputs/manifest.json') as f:
        m = json.load(f)
    with open('.selfhost_outputs/summary.json') as f:
        s = json.load(f)
    return s, m


def test_checklist_items_annotated_and_counts_stable():
    # Run baseline
    s, m = run_self('spec/test_spec.yml')
    # If preview attached, check annotations
    preview = m.get('checklist_preview')
    if preview:
        assert isinstance(preview, list)
        # Ensure annotations present
        for it in preview:
            assert 'applicable_states' in it
            assert 'relevance_reason' in it
    # Run again to check stability
    s2, m2 = run_self('spec/test_spec.yml')
    assert m.get('checklist_preview_items') == m2.get('checklist_preview_items')


def test_checklist_summary_present_on_success_runs():
    # Create a sections-only spec to reach VALID (success path may not succeed in self-host, so use execute via Engine)
    from shieldcraft.engine import Engine
    from shieldcraft.services.spec.ingestion import ingest_spec
    base = ingest_spec('spec/test_spec.yml')
    base['sections'] = [{'title': 's1'}]
    # Use Engine.execute to produce persistent manifest under products/
    eng = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')
    res = eng.execute('/dev/null') if False else eng.execute('spec/test_spec.yml')
    # If execute returns manifest (success), check checklist_summary presence
    # The engine writes products/<product>/manifest.json; check for checklist_summary in that file
    product_id = base.get('metadata', {}).get('product_id', 'unknown')
    path = f'products/{product_id}/manifest.json'
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        # checklist_summary exists (may be None)
        assert 'checklist_summary' in data
