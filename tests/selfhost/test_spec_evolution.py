import json
import os
import shutil


def _cleanup(product_id="unknown"):
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    lf = f"products/{product_id}/last_spec.json"
    if os.path.exists(lf):
        os.remove(lf)


def test_spec_evolution_present_on_initial_run():
    from shieldcraft.main import run_self_host

    _cleanup(product_id="test_spec")

    os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)

    assert os.path.exists('.selfhost_outputs/summary.json')
    assert os.path.exists('.selfhost_outputs/manifest.json')

    with open('.selfhost_outputs/summary.json') as f:
        summary = json.load(f)

    # spec_evolution should be present (advisory) even on first run
    se = summary.get('spec_evolution')
    assert se is not None
    assert 'summary' in se
    assert 'added' in se


def test_spec_evolution_detects_added_pointers_on_change(tmp_path):
    from shieldcraft.main import run_self_host

    # Start clean
    _cleanup(product_id="test_spec")

    os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # Create a modified spec by copying and adding a top-level dummy section
    with open('spec/test_spec.yml') as f:
        content = f.read()

    modified = content + "\n# Added section for evolution test\nextra_section:\n  foo: bar\n"
    mod_path = tmp_path / "test_spec_v2.yml"
    mod_path.write_text(modified)

    run_self_host(str(mod_path), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)

    assert os.path.exists('.selfhost_outputs/summary.json')
    with open('.selfhost_outputs/summary.json') as f:
        summary = json.load(f)

    se = summary.get('spec_evolution')
    assert se is not None
    # Expect at least one added pointer due to the new section
    assert se.get('summary', {}).get('added_count', 0) >= 1
