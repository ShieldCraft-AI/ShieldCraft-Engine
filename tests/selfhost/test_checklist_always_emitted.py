import json
import os
import shutil
import random
import string


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    import hashlib
    h = hashlib.sha256(open('artifacts/repo_sync_state.json','rb').read()).hexdigest()
    with open('repo_state_sync.json', 'w') as f:
        json.dump({"files":[{"path":"artifacts/repo_sync_state.json","sha256":h}]}, f)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def _random_text(n_words=100):
    words = ["".join(random.choices(string.ascii_lowercase, k=8)) for _ in range(n_words)]
    return "\n\n".join([" ".join(words[i:i+10]) for i in range(0, len(words), 10)])


def test_checklist_always_emitted_for_random_text(tmp_path):
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    # Write a random text file that will likely fail validation
    p = tmp_path / "random_spec.txt"
    p.write_text(_random_text(120), encoding='utf8')
    # Run self-host on the random text to trigger interpretation and potential validation failure
    run_self_host(str(p), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    # Assert checklist.json was written and has at least 5 items
    cj = '.selfhost_outputs/checklist.json'
    assert os.path.exists(cj), 'checklist.json is missing'
    cl = json.load(open(cj))
    assert isinstance(cl.get('items'), list)
    assert len(cl.get('items')) >= 5
    # requirements.json should be emitted alongside checklist.json
    rq = '.selfhost_outputs/requirements.json'
    assert os.path.exists(rq), 'requirements.json missing'
    rdata = json.loads(open(rq).read())
    assert 'requirements' in rdata and isinstance(rdata['requirements'], list)


def test_checklist_persisted_on_success():
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    cj = '.selfhost_outputs/checklist.json'
    assert os.path.exists(cj)
    cl = json.load(open(cj))
    assert isinstance(cl.get('items'), list)
    assert len(cl.get('items')) >= 1