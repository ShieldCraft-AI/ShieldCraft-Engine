import json
import os
import shutil


def _run(spec_path):
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)
    with open('.selfhost_outputs/summary.json') as f:
        s = json.load(f)
    with open('.selfhost_outputs/manifest.json') as f:
        m = json.load(f)
    return s, m


def test_baseline_guidance_contains_ordered_missing_and_checklist_explanation():
    s, m = _run('spec/test_spec.yml')
    # what_is_missing_next should be a list and ordered deterministically
    wn = s.get('what_is_missing_next') or []
    assert isinstance(wn, list)
    # checklist_preview_explanation should exist and be a string
    cpe = m.get('checklist_preview_explanation') or s.get('checklist_preview_explanation')
    assert isinstance(cpe, str)


def test_structured_guidance_explains_next_steps(tmp_path):
    from shieldcraft.services.spec.ingestion import ingest_spec
    base = ingest_spec('spec/test_spec.yml')
    md = dict(base)
    md['metadata'] = {'product_id': 'semantic-structured-test'}
    p = tmp_path / 'md.json'
    p.write_text(json.dumps(md, indent=2))
    s, m = _run(str(p))
    assert s.get('conversion_state') == 'STRUCTURED' or m.get('conversion_state') == 'STRUCTURED'
    # state_reason should be singular 'structured_threshold_met'
    assert s.get('state_reason') == 'structured_threshold_met'
    # what_is_missing_next should list the most impactful missing item first
    wn = s.get('what_is_missing_next') or []
    if wn:
        assert wn[0].get('code') in ('sections_empty', 'invariants_empty')
