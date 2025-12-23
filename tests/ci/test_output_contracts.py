import json
import os
import shutil
import tempfile
from pathlib import Path
import jsonschema

from shieldcraft.output_contracts import VERSION as OUTPUT_CONTRACT_VERSION
from shieldcraft.main import run_self_host

SCHEMA_DIR = Path("spec/schemas/output")


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    import hashlib
    h = hashlib.sha256(open('artifacts/repo_sync_state.json', 'rb').read()).hexdigest()
    with open('repo_state_sync.json', 'w') as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def _validate_against_schema(instance, schema_name):
    schema_path = SCHEMA_DIR / f"{schema_name}.schema.json"
    assert schema_path.exists(), f"schema missing: {schema_path}"
    schema = json.loads(schema_path.read_text())
    jsonschema.validate(instance=instance, schema=schema)


def test_valid_spec_emitted_artifacts_match_schemas():
    _prepare_env()
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec_path = str(repo_root / "demos" / "valid.json")
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # Checklist draft should exist and validate
    cd_path = Path('.selfhost_outputs') / 'checklist_draft.json'
    assert cd_path.exists()
    cd = json.loads(cd_path.read_text())
    _validate_against_schema(cd, 'checklist_draft')

    # Readiness trace may or may not be present; validate if present
    rt = Path('.selfhost_outputs') / 'readiness_trace.json'
    if rt.exists():
        rtj = json.loads(rt.read_text())
        _validate_against_schema(rtj, 'readiness_trace')

    # Spec feedback may or may not be emitted; if present, validate
    fb = Path('.selfhost_outputs') / 'spec_feedback.json'
    if fb.exists():
        fbj = json.loads(fb.read_text())
        _validate_against_schema(fbj, 'spec_feedback')

    # Ensure summary contains output_contract_version
    s = json.loads(open('.selfhost_outputs/summary.json', encoding='utf-8').read())
    assert s.get('output_contract_version') == OUTPUT_CONTRACT_VERSION


def test_invalid_spec_emits_feedback_and_suppressed_and_match_schemas():
    _prepare_env()
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as t:
        spec = {
            "metadata": {"product_id": "test-output-contract", "spec_format": "canonical_json_v1", "self_host": True},
            # Intentionally invalid shape
            "description": "This product must never leak"
        }
        json.dump(spec, t)
        tmp_path = t.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        run_self_host(tmp_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

        sup_path = Path('.selfhost_outputs') / 'suppressed_signal_report.json'
        assert sup_path.exists()
        sup = json.loads(sup_path.read_text())
        _validate_against_schema(sup, 'suppressed_signal_report')

        fb_path = Path('.selfhost_outputs') / 'spec_feedback.json'
        assert fb_path.exists()
        fb = json.loads(fb_path.read_text())
        _validate_against_schema(fb, 'spec_feedback')

        # Summary should include counts consistent with artifacts
        s = json.loads(open('.selfhost_outputs/summary.json', encoding='utf-8').read())
        assert s.get('output_contract_version') == OUTPUT_CONTRACT_VERSION
        assert s.get('suppressed_signal_count') == len(sup.get('suppressed', []))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
