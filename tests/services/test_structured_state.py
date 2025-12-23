import json
import os
import shutil


def run_and_read(spec_path):
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    with open('.selfhost_outputs/summary.json') as f:
        s = json.load(f)
    with open('.selfhost_outputs/manifest.json') as f:
        m = json.load(f)
    os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)
    return s, m


def test_baseline_not_structured():
    s, m = run_and_read('spec/test_spec.yml')
    # Baseline should not be classified as STRUCTURED by the new rule
    assert not (s.get('conversion_state') == 'STRUCTURED' or m.get('conversion_state') == 'STRUCTURED')


def test_single_section_metadata_model_instructions_structured(tmp_path):
    from shieldcraft.services.spec.ingestion import ingest_spec
    base = ingest_spec('spec/test_spec.yml')
    # metadata variant
    md = dict(base)
    md['metadata'] = {'product_id': 'semantic-structured-test'}
    md_path = tmp_path / 'md.json'
    md_path.write_text(json.dumps(md, indent=2))
    s, m = run_and_read(str(md_path))
    assert s.get('conversion_state') == 'STRUCTURED' or m.get('conversion_state') == 'STRUCTURED'

    # model variant
    mo = dict(base)
    mo['model'] = {'dependencies': []}
    mo_path = tmp_path / 'mo.json'
    mo_path.write_text(json.dumps(mo, indent=2))
    s, m = run_and_read(str(mo_path))
    assert s.get('conversion_state') == 'STRUCTURED' or m.get('conversion_state') == 'STRUCTURED'

    # instructions variant
    ins = dict(base)
    ins['instructions'] = [{'id': 'i1', 'type': 'noop'}]
    ins_path = tmp_path / 'ins.json'
    ins_path.write_text(json.dumps(ins, indent=2))
    s, m = run_and_read(str(ins_path))
    assert s.get('conversion_state') == 'STRUCTURED' or m.get('conversion_state') == 'STRUCTURED'


def test_sections_only_produces_valid(tmp_path):
    from shieldcraft.services.spec.ingestion import ingest_spec
    base = ingest_spec('spec/test_spec.yml')
    sec = dict(base)
    sec['sections'] = [{'title': 's1'}]
    sec_path = tmp_path / 'sec.json'
    sec_path.write_text(json.dumps(sec, indent=2))
    s, m = run_and_read(str(sec_path))
    # When sections provided, engine should reach VALID (per prior behavior)
    assert s.get('conversion_state') == 'VALID' or m.get('conversion_state') == 'VALID'
