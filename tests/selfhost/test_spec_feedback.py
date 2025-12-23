import json
import os
import tempfile
import shutil


def test_spec_feedback_written_on_validation_failure():
    """When validation fails, `spec_feedback.json` should be emitted and include missing sections."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as t:
        spec = {
            "metadata": {"product_id": "feedback-test", "version": "1.0", "spec_format": "canonical_json_v1", "self_host": True},
            # Intentionally invalid: missing 'sections'
        }
        json.dump(spec, t)
        tmp_path = t.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')

        run_self_host(tmp_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

        fb_path = os.path.join('.selfhost_outputs', 'spec_feedback.json')
        assert os.path.exists(fb_path), 'spec_feedback.json not written on validation failure'
        with open(fb_path) as f:
            fb = json.load(f)
        assert 'missing_sections' in fb
        assert 'sections' in fb.get('missing_sections', [])
        assert 'suggested_next_edits' in fb
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_spec_feedback_includes_remediation_hints_on_readiness_failure(monkeypatch):
    """If readiness fails (tests_attached), spec_feedback should include remediation hints."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as t:
        spec = {
            "metadata": {"product_id": "feedback-test-2", "version": "1.0", "spec_format": "canonical_json_v1", "self_host": True},
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

        os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
        run_self_host(tmp_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)

        fb_path = os.path.join('.selfhost_outputs', 'spec_feedback.json')
        assert os.path.exists(fb_path), 'spec_feedback.json not written on readiness failure'
        with open(fb_path) as f:
            fb = json.load(f)
        assert fb.get('remediation_hints_count', 0) > 0
        assert isinstance(fb.get('suggested_next_edits'), list)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
