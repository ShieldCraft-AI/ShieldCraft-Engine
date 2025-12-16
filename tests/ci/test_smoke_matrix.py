import json
import os
import tempfile
import shutil


def test_cli_self_host_success():
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {"metadata": {"product_id": "smoke", "spec_format": "canonical_json_v1", "self_host": True}, "model": {}, "sections": {}}
        json.dump(spec, tmp)
        path = tmp.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        # Ensure sync artifact exists and worktree is considered clean
        os.makedirs('artifacts', exist_ok=True)
        open('artifacts/repo_sync_state.json', 'w').write('{}')
        import hashlib
        h = hashlib.sha256(open('artifacts/repo_sync_state.json','rb').read()).hexdigest()
        with open('repo_state_sync.json','w') as f:
            json.dump({"files":[{"path":"artifacts/repo_sync_state.json","sha256":h}]}, f)
        import importlib
        importlib.import_module('shieldcraft.persona')
        import shieldcraft.persona as pmod
        setattr(pmod, '_is_worktree_clean', lambda: True)
        run_self_host(path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        assert os.path.exists('.selfhost_outputs/manifest.json')
        assert os.path.exists('.selfhost_outputs/summary.json')
        # Assert conversion_path and execution_preview behavior for non-READY states
        s = json.loads(open('.selfhost_outputs/summary.json').read())
        assert 'conversion_path' in s
        if s.get('conversion_state') != 'READY':
            assert s['conversion_path']['blocking_requirements'], 'conversion_path must not be empty for non-READY states'
            # execution_preview should be present for STRUCTURED/VALID and hypothetical
            if s.get('conversion_state') in ('STRUCTURED', 'VALID'):
                assert 'execution_preview' in s and s['execution_preview']['hypothetical'] is True
            else:
                assert 'execution_preview' not in s
    finally:
        os.unlink(path)


def test_cli_self_host_invalid_spec():
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {"metadata": {"product_id": "smoke", "self_host": True}, "invalid": True}
        json.dump(spec, tmp)
        path = tmp.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        # Ensure sync artifact and clean worktree to reach validation stage
        os.makedirs('artifacts', exist_ok=True)
        open('artifacts/repo_sync_state.json', 'w').write('{}')
        import hashlib
        h = hashlib.sha256(open('artifacts/repo_sync_state.json','rb').read()).hexdigest()
        with open('repo_state_sync.json','w') as f:
            json.dump({"files":[{"path":"artifacts/repo_sync_state.json","sha256":h}]}, f)
        import importlib
        importlib.import_module('shieldcraft.persona')
        import shieldcraft.persona as pmod
        setattr(pmod, '_is_worktree_clean', lambda: True)
        run_self_host(path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        # Accept either structured errors.json or generic error.txt
        assert os.path.exists('.selfhost_outputs/errors.json') or os.path.exists('.selfhost_outputs/error.txt')
        # Partial manifest may be emitted to assist authors (conversion/diagnostic info)
        # Checklist draft is now emitted for author visibility even on validation failure
        # spec_feedback.json may also be emitted to provide remediation guidance
        assert set([p for p in os.listdir('.selfhost_outputs') if not p.startswith('.')]) <= {'errors.json', 'summary.json', 'manifest.json', 'checklist_draft.json', 'spec_feedback.json', 'checklist.json'}
        # Summary should contain conversion_path to help authors make progress
        s = json.loads(open('.selfhost_outputs/summary.json').read())
        assert 'conversion_path' in s
        assert s['conversion_path']['blocking_requirements'], 'conversion_path must not be empty for non-READY states'
        # And summary should indicate that a checklist draft was emitted
        assert s.get('checklist_emitted') is True
        assert s.get('checklist_status') == 'draft'
    finally:
        os.unlink(path)


def test_progress_summary_integration():
    from shieldcraft.main import run_self_host

    # First run: good spec
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {"metadata": {"product_id": "smoke_progress", "spec_format": "canonical_json_v1", "self_host": True}, "model": {"a": 1}, "sections": [{}]}
        json.dump(spec, tmp)
        path1 = tmp.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        # Ensure sync artifact exists and worktree is considered clean
        os.makedirs('artifacts', exist_ok=True)
        open('artifacts/repo_sync_state.json', 'w').write('{}')
        import hashlib
        h = hashlib.sha256(open('artifacts/repo_sync_state.json','rb').read()).hexdigest()
        with open('repo_state_sync.json','w') as f:
            json.dump({"files":[{"path":"artifacts/repo_sync_state.json","sha256":h}]}, f)
        import importlib
        importlib.import_module('shieldcraft.persona')
        import shieldcraft.persona as pmod
        setattr(pmod, '_is_worktree_clean', lambda: True)
        run_self_host(path1, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        s1 = json.loads(open('.selfhost_outputs/summary.json').read())
        assert 'progress_summary' in s1
        assert s1['progress_summary']['delta'] in ('initial', 'advanced', 'unchanged', 'regressed')
        # Ensure last_state was persisted for this product
        assert os.path.exists('products/smoke_progress/last_state.json')
        ls = json.loads(open('products/smoke_progress/last_state.json').read())
        assert ls.get('conversion_state') is not None
    finally:
        os.unlink(path1)

    # Second run: regress (missing model)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {"metadata": {"product_id": "smoke_progress", "self_host": True}, "invalid": True}
        json.dump(spec, tmp)
        path2 = tmp.name

    try:
        run_self_host(path2, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        s2 = json.loads(open('.selfhost_outputs/summary.json').read())
        assert 'progress_summary' in s2
        # When validation fails we have no authoritative fingerprint for the current run
        # so we must treat this as a first-observation for progress (no false regression)
        assert s2['progress_summary']['delta'] == 'initial'
        assert s2['progress_summary'].get('reasons') is not None
    finally:
        os.unlink(path2)
