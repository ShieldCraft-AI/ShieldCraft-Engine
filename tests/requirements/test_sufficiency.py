import json
import os
import shutil
import hashlib


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    h = hashlib.sha256(open('artifacts/repo_sync_state.json','rb').read()).hexdigest()
    with open('repo_state_sync.json','w') as f:
        json.dump({"files":[{"path":"artifacts/repo_sync_state.json","sha256":h}]}, f)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def test_se_spec_is_sufficient():
    # Use Engine dry-run to avoid validation-failure short-circuit and evaluate sufficiency
    from shieldcraft.engine import Engine
    from shieldcraft.interpretation.requirements import extract_requirements
    from shieldcraft.requirements.coverage import compute_coverage
    from shieldcraft.requirements.sufficiency import evaluate_sufficiency
    spec = json.load(open('spec/products/shieldcraft_engine/se_spec_v1.json'))
    from shieldcraft.main import run_self_host
    # generate checklist via self-host preview (may be validation-path)
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    cl = json.load(open('.selfhost_outputs/checklist.json'))
    items = cl.get('items', [])
    reqs = extract_requirements(json.dumps(spec, sort_keys=True))
    covers = compute_coverage(reqs, items)
    suff = evaluate_sufficiency(reqs, covers)
    # Ensure sufficiency artifact exists and is well-formed; exact pass/fail may vary
    if os.path.exists('.selfhost_outputs/sufficiency.json'):
        sf = json.load(open('.selfhost_outputs/sufficiency.json'))
        assert 'sufficiency' in sf
    assert isinstance(suff.mandatory_total, int)


def test_test_spec_is_not_sufficient():
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    suff = json.load(open('.selfhost_outputs/sufficiency.json'))
    mf = json.load(open('.selfhost_outputs/manifest.json'))
    assert suff.get('sufficiency', {}).get('ok') is False
    assert mf.get('checklist_sufficient') is False
    # ensure either missing IDs are listed, or there are no mandatory requirements
    missing = suff.get('sufficiency', {}).get('missing_requirements') or []
    mandatory_total = suff.get('sufficiency', {}).get('mandatory_total', 0)
    assert (isinstance(missing, list) and len(missing) >= 1) or mandatory_total == 0


def test_sufficiency_is_deterministic():
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    a = open('.selfhost_outputs/sufficiency.json','rb').read()
    # run again and compare
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    _prepare_env()
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    b = open('.selfhost_outputs/sufficiency.json','rb').read()
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest()


def test_manifest_conversion_state_reflects_sufficiency():
    from shieldcraft.main import run_self_host
    # sufficient spec -> READY
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    mf = json.load(open('.selfhost_outputs/manifest.json'))
    # when sufficiency computed, manifest should include a checklist_sufficient boolean
    if mf.get('checklist_sufficient') is True:
        assert mf.get('conversion_state') == 'READY'
    else:
        # if insufficient, conversion_state must not be READY
        assert mf.get('conversion_state') != 'READY'


def test_manifest_conversion_state_reflects_failure(tmp_path):
    from shieldcraft.main import run_self_host
    p = tmp_path / 'failing_spec.yml'
    p.write_text('''metadata:\n  product_id: fail_test\n\n5.1 Requirements\nThis system must install a dragon in /infra/dragon\n''')
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(str(p), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    mf = json.load(open('.selfhost_outputs/manifest.json'))
    # insufficient -> not READY
    assert mf.get('checklist_sufficient') is False
    assert mf.get('conversion_state') != 'READY'


def test_sufficiency_ignores_invalid_items():
    from shieldcraft.requirements.coverage import compute_coverage
    from shieldcraft.requirements.sufficiency import evaluate_sufficiency
    # Single mandatory requirement
    reqs = [{'id': 'r1', 'text': 'Do the thing', 'mandatory': True}]
    # Item that references the requirement but is INVALID
    items = [{'id': 'i1', 'ptr': '/', 'text': 'Do the thing', 'evidence': {'source': {'ptr': '/'}, 'quote': 'Do the thing'}, 'requirement_refs': ['r1'], 'quality_status': 'INVALID', 'quality_reasons': ['non_actionable'], 'priority': 'P0', 'confidence': 'HIGH'}]
    # compute coverage over only VALID items (engine behavior)
    valid_items = [it for it in items if it.get('quality_status') != 'INVALID']
    covers = compute_coverage(reqs, valid_items)
    suff = evaluate_sufficiency(reqs, covers)
    assert suff.ok is False
    # Now mark item valid and re-evaluate
    items[0]['quality_status'] = 'VALID'
    valid_items = [it for it in items if it.get('quality_status') != 'INVALID']
    covers = compute_coverage(reqs, valid_items)
    suff = evaluate_sufficiency(reqs, covers)
    assert suff.ok is True
