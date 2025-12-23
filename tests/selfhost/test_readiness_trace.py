import json
import os
import tempfile
import shutil


def test_readiness_trace_maps_tests_attached_to_items(monkeypatch):
    """If readiness gate 'tests_attached' fails, readiness_trace.json should map it to checklist items."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as t:
        spec = {
            "metadata": {"product_id": "trace-test", "version": "1.0", "spec_format": "canonical_json_v1", "self_host": True},
            "model": {"version": "1.0"},
            "sections": [{"id": "core", "description": "Core must have tests attached"}],
        }
        json.dump(spec, t)
        tmp_path = t.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')

        # Force tests_attached gate to fail
        monkeypatch.setattr(
            'shieldcraft.verification.readiness_evaluator.enforce_tests_attached',
            lambda items: (
                _ for _ in ()).throw(
                RuntimeError('no tests')))

        # Allow dirty worktree for test isolation
        os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
        run_self_host(tmp_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)

        rt_path = os.path.join('.selfhost_outputs', 'readiness_trace.json')
        assert os.path.exists(rt_path), 'readiness_trace.json not written'
        with open(rt_path) as f:
            data = json.load(f)
        assert 'trace' in data and 'tests_attached' in data['trace']
        ta = data['trace']['tests_attached']
        assert isinstance(ta.get('item_ids'), list) and len(ta.get('item_ids')) > 0

        with open('.selfhost_outputs/summary.json') as f:
            s = json.load(f)
        assert s.get('readiness_blockers_count', 0) >= 1
        assert isinstance(s.get('readiness_blocker_item_ids', []), list)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
