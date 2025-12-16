import json
import os
import tempfile
import shutil
import pytest


def _write_spec(tmpfile, spec):
    with open(tmpfile, 'w') as f:
        json.dump(spec, f)


def test_invalid_spec_blocks_readiness():
    """An invalid spec (fails semantic strictness) should produce validity fail
    and readiness should be marked 'not_evaluated'."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as t:
        spec = {
            "metadata": {
                "product_id": "invalid-spec",
                "version": "1.0",
                "spec_format": "canonical_json_v1",
                "self_host": True,
            },
            # Intentionally omit 'sections' to trigger sections_empty (Level1)
            "model": {"version": "1.0"}
        }
        _write_spec(t.name, spec)
        tmp_path = t.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        run_self_host(tmp_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

        # Expect errors.json and summary.json
        assert os.path.exists('.selfhost_outputs/errors.json')
        assert os.path.exists('.selfhost_outputs/summary.json')

        with open('.selfhost_outputs/summary.json') as f:
            summary = json.load(f)

        assert summary.get('validity_status') == 'fail'
        assert summary.get('readiness_status') == 'not_evaluated'
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_valid_but_not_ready(monkeypatch):
    """A spec that is valid but fails readiness gates should be validity=pass and readiness=fail."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as t:
        spec = {
            "metadata": {"product_id": "valid-not-ready", "version": "1.0", "spec_format": "canonical_json_v1", "self_host": True},
            "model": {"version": "1.0"},
            "sections": [{"id": "core", "description": "Core"}],
        }
        _write_spec(t.name, spec)
        tmp_path = t.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')

        # Force tests_attached gate to fail
        monkeypatch.setattr('shieldcraft.verification.readiness_evaluator.enforce_tests_attached', lambda items: (_ for _ in ()).throw(RuntimeError('no tests')))

        # Allow dirty worktree for test isolation
        os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
        run_self_host(tmp_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)

        assert os.path.exists('.selfhost_outputs/summary.json')
        with open('.selfhost_outputs/summary.json') as f:
            summary = json.load(f)

        assert summary.get('validity_status') == 'pass'
        assert summary.get('readiness_status') == 'fail'
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_valid_and_ready(monkeypatch):
    """A spec that is valid and passes readiness gates should show both pass."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as t:
        spec = {
            "metadata": {"product_id": "valid-ready", "version": "1.0", "spec_format": "canonical_json_v1", "self_host": True},
            "model": {"version": "1.0"},
            "sections": [{"id": "core", "description": "Core"}],
        }
        _write_spec(t.name, spec)
        tmp_path = t.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')

        # Make readiness gates no-ops / succeed
        monkeypatch.setattr('shieldcraft.verification.readiness_evaluator.enforce_tests_attached', lambda items: None)
        monkeypatch.setattr('shieldcraft.verification.readiness_evaluator.enforce_spec_fuzz_stability', lambda s, g, max_variants=3: None)
        monkeypatch.setattr('shieldcraft.verification.readiness_evaluator.enforce_persona_veto', lambda e: None)
        monkeypatch.setattr('shieldcraft.verification.readiness_evaluator.replay_and_compare', lambda engine, det: {'match': True})

        # Allow dirty worktree for test isolation
        os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
        run_self_host(tmp_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)

        assert os.path.exists('.selfhost_outputs/summary.json')
        with open('.selfhost_outputs/summary.json') as f:
            summary = json.load(f)

        assert summary.get('validity_status') == 'pass'
        assert summary.get('readiness_status') == 'pass'
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
