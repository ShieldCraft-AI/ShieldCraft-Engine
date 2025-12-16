import json
import os
import shutil


def test_normalized_skeleton_emits_partial_artifacts():
    from shieldcraft.main import run_self_host

    # Use provided test_spec.yml (a normalized DSL skeleton fixture)
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    # Allow dirty worktree in tests
    os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)

    assert os.path.exists('.selfhost_outputs/summary.json')
    assert os.path.exists('.selfhost_outputs/manifest.json')

    with open('.selfhost_outputs/manifest.json') as f:
        manifest = json.load(f)

    with open('.selfhost_outputs/summary.json') as f:
        summary = json.load(f)

    assert manifest.get('partial') is True
    assert manifest.get('conversion_tier') == 'convertible'
    assert manifest.get('conversion_state') == 'CONVERTIBLE'
    assert summary.get('conversion_tier') == 'convertible'
    assert isinstance(summary.get('what_is_missing_next'), list) or 'errors' in summary
