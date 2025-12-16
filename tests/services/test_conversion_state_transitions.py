import json
import os
import shutil
import tempfile


def test_raw_envelope_is_accepted():
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    envelope = {"metadata": {"normalized": True, "source_format": "yaml"}, "raw_input": "x"}
    res = engine.run_self_host(envelope, dry_run=True)
    assert isinstance(res, dict)
    assert res.get("manifest", {}).get("conversion_state") == "ACCEPTED"


def test_normalized_skeleton_is_convertible():
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)
    with open('.selfhost_outputs/manifest.json') as f:
        manifest = json.load(f)
    assert manifest.get('conversion_state') == 'CONVERTIBLE'


def test_valid_spec_sets_valid_state():
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = {"metadata": {"product_id": "t", "spec_format": "canonical_json_v1", "spec_version": "1.0"}, "model": {"version": "1.0"}, "sections": [{"id": "s"}]}
    engine.preflight(spec)
    assert engine.conversion_state == engine._ConversionState.VALID


def test_ready_spec_sets_ready_state(monkeypatch, tmp_path):
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Ensure readiness gates succeed
    monkeypatch.setattr('shieldcraft.verification.readiness_evaluator.enforce_tests_attached', lambda items: None)
    monkeypatch.setattr('shieldcraft.verification.readiness_evaluator.enforce_spec_fuzz_stability', lambda s, g, max_variants=3: None)
    monkeypatch.setattr('shieldcraft.verification.readiness_evaluator.enforce_persona_veto', lambda e: None)
    monkeypatch.setattr('shieldcraft.verification.readiness_evaluator.replay_and_compare', lambda engine, det: {'match': True})

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {
            "metadata": {"product_id": "ready-product", "version": "1.0", "spec_format": "canonical_json_v1", "self_host": True},
            "model": {"version": "1.0"},
            "sections": [{"id": "core"}],
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    try:
        os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
        from shieldcraft.main import run_self_host
        run_self_host(tmp_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        with open('.selfhost_outputs/manifest.json') as f:
            manifest = json.load(f)
        assert manifest.get('conversion_state') == 'READY'
    finally:
        os.unlink(tmp_path)
        os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)
