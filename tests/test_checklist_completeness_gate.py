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
    # Check completeness report was emitted and contains uncovered entry
    rep = json.load(open('.selfhost_outputs/completeness_report.json'))
    assert rep.get('uncovered_must') and len(rep['uncovered_must']) >= 1
    # Manifest should reflect INCOMPLETE conversion_state
    manifest = json.load(open('.selfhost_outputs/manifest.json'))
    assert manifest.get('conversion_state') == 'INCOMPLETE'
