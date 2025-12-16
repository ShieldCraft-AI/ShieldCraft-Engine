import json
import os
import shutil
import tempfile
from pathlib import Path

from scripts.run_spec_trials import run_trials


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    import hashlib
    h = hashlib.sha256(open('artifacts/repo_sync_state.json','rb').read()).hexdigest()
    with open('repo_state_sync.json', 'w') as f:
        json.dump({"files":[{"path":"artifacts/repo_sync_state.json","sha256":h}]}, f)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def test_runner_handles_empty_directory(tmp_path):
    _prepare_env()
    out = tmp_path / "report.json"
    artifacts = tmp_path / "artifacts"
    out_path = run_trials(str(tmp_path), out_report=str(out), raw_artifacts_dir=str(artifacts))
    assert os.path.exists(out_path)
    r = json.loads(open(out_path).read())
    assert r["results"] == []


def test_runner_records_checklist_fields(tmp_path):
    _prepare_env()
    # Create an invalid spec (will be validated by engine)
    specdir = tmp_path / "specs"
    specdir.mkdir()
    sp = specdir / "bad.yml"
    sp.write_text("invalid: true")

    out = tmp_path / "report.json"
    artifacts = tmp_path / "artifacts"
    out_path = run_trials(str(specdir), out_report=str(out), raw_artifacts_dir=str(artifacts))
    assert os.path.exists(out_path)
    r = json.loads(open(out_path).read())
    assert len(r["results"]) == 1
    res = r["results"][0]
    assert res.get("error_codes")
    # Ensure checklist fields recorded
    assert res.get("checklist_emitted") is True
    assert isinstance(res.get("checklist_item_count"), int)


def test_runner_fails_when_checklist_missing(tmp_path, monkeypatch):
    _prepare_env()
    # Create a spec file to trigger ingest
    specdir = tmp_path / "specs"
    specdir.mkdir()
    sp = specdir / "broken.yml"
    sp.write_text("invalid: true")

    # Monkeypatch import_module to simulate ingest_spec raising
    import importlib
    real_import = importlib.import_module

    def fake_import(name):
        if name == "shieldcraft.services.spec.ingestion":
            class Dummy:
                def ingest_spec(self, path):
                    raise RuntimeError("ingest failure simulated")
            return Dummy()
        return real_import(name)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    out = tmp_path / "report.json"
    artifacts = tmp_path / "artifacts"
    try:
        run_trials(str(specdir), out_report=str(out), raw_artifacts_dir=str(artifacts))
        assert False, "Expected AssertionError due to missing checklist"
    except AssertionError:
        pass


def test_runner_handles_invalid_spec(tmp_path):
    _prepare_env()
    # Create an invalid spec (missing required 'sections' -> will fail validation)
    specdir = tmp_path / "specs"
    specdir.mkdir()
    sp = specdir / "bad.yml"
    sp.write_text("invalid: true")

    out = tmp_path / "report.json"
    artifacts = tmp_path / "artifacts"
    out_path = run_trials(str(specdir), out_report=str(out), raw_artifacts_dir=str(artifacts))
    assert os.path.exists(out_path)
    r = json.loads(open(out_path).read())
    assert len(r["results"]) == 1
    res = r["results"][0]
    # For invalid spec we should have error_codes and an errors.json artifact
    assert res.get("error_codes")
    # Raw artifacts must exist for that spec
    art_dirs = list(Path(str(artifacts)).glob("*"))
    assert art_dirs, "Artifacts directory should contain per-spec artifacts"
