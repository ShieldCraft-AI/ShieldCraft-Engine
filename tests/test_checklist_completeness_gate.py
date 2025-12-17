import json
import os
import shutil
from shieldcraft.requirements.extractor import extract_requirements
from shieldcraft.verification.completeness_gate import evaluate_completeness


def test_litmus_passes_completeness():
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    cl = json.load(open('.selfhost_outputs/checklist.json'))
    items = cl.get('items') or []
    reqs = extract_requirements(open('spec/test_spec.yml','r',encoding='utf8').read())
    report = evaluate_completeness(reqs, items)
    assert report.get('complete') is True


def test_synthetic_failure_reports_uncovered(tmp_path):
    # Create a spec with a MUST that cannot be covered
    spec = tmp_path / 'failing_spec.yml'
    spec.write_text('''metadata:\n  product_id: fail_test\n\n5.1 Requirements\nThis system must install a dragon in /infra/dragon\n''')
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(str(spec), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    # Check completeness report was emitted and contains uncovered entry (compat fallback)
    if os.path.exists('.selfhost_outputs/completeness_report.json'):
        rep = json.load(open('.selfhost_outputs/completeness_report.json'))
    else:
        # older compatibility artifact
        rep = json.load(open('.selfhost_outputs/requirement_completeness.json'))
    # allow either shape: legacy completeness_report (uncovered_must/uncovered) or requirement_completeness (requirements/state)
    uncovered = None
    if 'uncovered_must' in rep or 'uncovered' in rep:
        uncovered = rep.get('uncovered_must') or rep.get('uncovered')
    elif 'requirements' in rep:
        # any requirement not COMPLETE is considered uncovered/weak
        uncovered = [r for r in rep.get('requirements', []) if r.get('state') != 'COMPLETE']
    assert uncovered and len(uncovered) >= 1
    # Manifest should reflect INCOMPLETE conversion_state
    manifest = json.load(open('.selfhost_outputs/manifest.json'))
    # Accept either explicit INCOMPLETE conversion_state or a checklist_sufficient False flag
    assert manifest.get('conversion_state') == 'INCOMPLETE' or manifest.get('checklist_sufficient') is False
