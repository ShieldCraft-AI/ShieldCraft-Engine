import json
import os
import shutil
from pathlib import Path
from shieldcraft.main import run_self_host


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


def test_senior_engineer_sanity_with_prose_spec():
    _prepare_env()
    spec_path = 'spec/test_spec.yml'
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # Checklist exists
    cd_path = Path('.selfhost_outputs') / 'checklist_draft.json'
    assert cd_path.exists(), 'checklist_draft.json is missing'
    cd = json.loads(cd_path.read_text())
    items = cd.get('items', [])
    assert isinstance(items, list)
    assert len(items) > 0, 'checklist_item_count must be > 0 for prose-heavy spec'

    # At least one actionable item (confidence != low) OR a refusal is present
    has_actionable = any((it.get('confidence') or 'medium') in ('high', 'medium') for it in items)
    rr_path = Path('.selfhost_outputs') / 'refusal_report.json'
    assert has_actionable or rr_path.exists(), 'No actionable item (non-low confidence) and no refusal emitted'

    # Spec feedback exists with next actions
    fb_path = Path('.selfhost_outputs') / 'spec_feedback.json'
    assert fb_path.exists(), 'spec_feedback.json missing'
    fb = json.loads(fb_path.read_text())
    assert 'suggested_next_edits' in fb and isinstance(fb.get('suggested_next_edits'), list), 'spec_feedback missing suggested_next_edits'

    # Human-facing summary fields
    s = json.loads(open('.selfhost_outputs/summary.json').read())
    assert 'is_it_safe_to_act' in s and s.get('is_it_safe_to_act') in ('yes', 'no', 'unknown')
    if s.get('is_it_safe_to_act') == 'yes':
        assert 'where_is_safe' in s and isinstance(s.get('where_is_safe'), list) and len(s.get('where_is_safe')) > 0
    if s.get('is_it_safe_to_act') == 'no':
        assert 'why_not_safe' in s and s.get('why_not_safe')
