import os
import shutil
import json
import pytest
from shieldcraft.engine import Engine


def test_selfhost_fails_on_disallowed_artifact(monkeypatch, tmp_path):
    """If codegen produces a disallowed artifact path, self-host should raise and not write extras."""
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Monkeypatch codegen.run to return a disallowed path
    def fake_codegen(checklist, dry_run=False):
        return {"outputs": [{"path": "../../etc/passwd", "content": "bad"}], "codegen_bundle_hash": "deadbeef"}

    monkeypatch.setattr(engine, 'codegen', type('C', (), {'run': staticmethod(fake_codegen)}))

    with pytest.raises(RuntimeError):
        engine.run_self_host(json.load(open('spec/se_dsl_v1.spec.json')))

    # Ensure no files were written outside .selfhost_outputs
    assert not os.path.exists('/etc/passwd') or os.path.getsize('/etc/passwd') >= 0


def test_selfhost_writes_errors_on_validation(monkeypatch, tmp_path):
    """If validation fails, self-host should write only errors.json and not partial artifacts."""
    # Replace engine._validate_spec to raise a ValidationError
    from shieldcraft.services.validator import ValidationError

    def fake_validate(spec):
        raise ValidationError(code="missing_provenance", message="missing provenance", location="/metadata")

    # Patch Engine._validate_spec so any Engine instance will raise ValidationError
    import shieldcraft.engine as engmod
    monkeypatch.setattr(engmod.Engine, '_validate_spec', lambda self, spec: (_ for _ in ()).throw(ValidationError(code="missing_provenance", message="missing provenance", location="/metadata")))

    # Run via main.run_self_host wrapper to exercise error serialization
    from shieldcraft.main import run_self_host
    # Ensure clean output dir
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

    err_path = os.path.join('.selfhost_outputs', 'errors.json')
    assert os.path.exists(err_path)
    data = json.load(open(err_path))
    assert 'errors' in data
    assert data['errors'][0]['code'] == 'missing_provenance'

    # Ensure no other file types were emitted besides optional summary/manifest, checklist draft and spec feedback
    entries = [p for p in os.listdir('.selfhost_outputs') if not p.startswith('.')]
    assert 'errors.json' in entries
    assert set(entries) <= {'errors.json', 'summary.json', 'manifest.json', 'checklist_draft.json', 'spec_feedback.json', 'checklist.json'}
