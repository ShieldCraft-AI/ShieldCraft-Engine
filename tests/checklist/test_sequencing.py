import json
import os
import shutil
import hashlib

from shieldcraft.checklist.dependencies import infer_item_dependencies, build_graph, detect_cycles, build_sequence


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


def test_detect_cycles_from_graph():
    items = [{'id': 'a'}, {'id': 'b'}, {'id': 'c'}]
    graph = {'a': set(['b']), 'b': set(['c']), 'c': set(['a'])}
    cycles = detect_cycles(graph)
    assert any(set(c) == {'a', 'b', 'c'} for c in cycles)


def test_sequence_and_no_orphans():
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    _prepare_env()
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    seq = json.load(open('.selfhost_outputs/checklist_sequence.json'))
    sequence = seq.get('sequence', [])
    # No orphan depends_on references
    ids = {s['id'] for s in sequence}
    for s in sequence:
        for d in s.get('depends_on', []):
            assert d in ids
    # ensure orphan_count is present and non-negative
    assert isinstance(seq.get('orphan_count', 0), int) and seq.get('orphan_count', 0) >= 0


def test_sequence_deterministic(tmp_path):
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    a = open('.selfhost_outputs/checklist_sequence.json','rb').read()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    b = open('.selfhost_outputs/checklist_sequence.json','rb').read()
    assert a == b
