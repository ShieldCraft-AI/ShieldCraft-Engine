import json
import os
import shutil


def test_strictness_enforcement_includes_governance():
    from shieldcraft.main import run_self_host

    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    # Enable level 2 to trigger MODEL_EMPTY / INVARIANTS_EMPTY enforcement
    os.environ['SEMANTIC_STRICTNESS_LEVEL_2'] = '1'
    os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    os.environ.pop('SEMANTIC_STRICTNESS_LEVEL_2', None)
    os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)

    with open('.selfhost_outputs/summary.json') as f:
        summary = json.load(f)

    # Expect summary to reference governance_enforcements
    ge = summary.get('governance_enforcements')
    assert isinstance(ge, list)
    # If there's an enforcement, it should include governance source metadata
    if len(ge) > 0:
        g0 = ge[0]
        assert 'code' in g0
        gov = g0.get('governance')
        assert gov is None or ('file' in gov and 'file_hash' in gov)
