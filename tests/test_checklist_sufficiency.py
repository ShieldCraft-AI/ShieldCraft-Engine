import json
import os
import shutil
from shieldcraft.requirements.extractor import extract_requirements
from shieldcraft.verification.coverage import map_requirements_to_checklist, write_sufficiency_report


def test_litmus_checklist_covers_requirements():
    from shieldcraft.main import run_self_host
    # prepare env and run self-host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # load checklist
    p = os.path.join('.selfhost_outputs', 'checklist.json')
    assert os.path.exists(p), 'checklist.json missing'
    cl = json.load(open(p))
    items = cl.get('items') or []

    # extract canonical requirements
    text = open('spec/test_spec.yml', 'r', encoding='utf8').read()
    reqs = extract_requirements(text)

    # map and evaluate coverage
    res = map_requirements_to_checklist(reqs, items)
    uncovered = [
        r for r in res['uncovered'] if any(
            k in (
                r.get('text') or '').lower() for k in [
                'must',
                'shall',
                'requires',
                'mandatory',
                'enforced',
                'every run must'])]

    report = {
        'total_requirements': len(reqs),
        'covered': len(res['covered']),
        'uncovered': len(res['uncovered']),
        'weakly_covered': len(res['weakly_covered']),
        'uncovered_list': res['uncovered'],
    }
    write_sufficiency_report(report, outdir='.selfhost_outputs')

    assert not uncovered, f"Uncovered MUST requirements: {uncovered}"
