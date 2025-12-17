import json
import os
import shutil
import hashlib


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def test_se_spec_is_implementable():
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    mf = json.load(open('.selfhost_outputs/manifest.json'))
    rc = json.load(open('.selfhost_outputs/requirement_completeness.json'))
    pct = rc.get('summary', {}).get('complete_pct', 0.0)
    impl = mf.get('implementability', {}).get('implementable')
    assert (impl is True) or (pct >= 0.98)


def test_prose_is_not_implementable(tmp_path):
    from shieldcraft.main import run_self_host
    p = tmp_path / 'prose.yml'
    p.write_text('''metadata:\n  product_id: prose_test\n\nThis is a prose-only document that mentions must but no concrete action or reference.''')
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(str(p), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    rc = json.load(open('.selfhost_outputs/requirement_completeness.json'))
    pct = rc.get('summary', {}).get('complete_pct', 0.0)
    mf = json.load(open('.selfhost_outputs/manifest.json'))
    impl = mf.get('implementability', {}).get('implementable')
    assert (impl is False) or (pct < 0.98)


def test_completeness_deterministic():
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    a = open('.selfhost_outputs/requirement_completeness.json','rb').read()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    _prepare_env()
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    b = open('.selfhost_outputs/requirement_completeness.json','rb').read()
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest()
