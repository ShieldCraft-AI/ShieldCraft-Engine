import importlib.util
import json
from pathlib import Path


def load_module(path: str):
    spec = importlib.util.spec_from_file_location("canonical_full_run_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_canonical_full_run_determinism(tmp_path, monkeypatch):
    # Set env vars similar to script expectations
    monkeypatch.delenv("SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT", raising=False)
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "1")
    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")

    script_path = Path("scripts/canonical_full_run.py").resolve()
    mod = load_module(str(script_path))

    # Redirect OUT_DIR to tmp dir to avoid polluting repo
    out_dir = tmp_path / "canonical_full_run"
    mod.OUT_DIR = out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    run1_dir, _ = mod.run_once("run1")
    run2_dir, _ = mod.run_once("run2")

    p1 = (Path(run1_dir) / "canonical_preview.json").read_text()
    p2 = (Path(run2_dir) / "canonical_preview.json").read_text()
    assert p1 == p2, "Canonical preview digests must match across runs"

    # Produce summary.json similar to script
    clist = json.loads((Path(run1_dir) / "generated_checklist.json").read_text())
    checklist_item_count = len(clist) if isinstance(clist, list) else 0
    tests = json.loads((Path(run1_dir) / "generated_test_plan.json").read_text()).get("tests", [])
    persona_events = 0
    pe = Path(run1_dir) / "persona_events_v1.json"
    if pe.exists():
        persona_events = len(json.loads(pe.read_text()))

    summary = {
        "checklist_item_count": checklist_item_count,
        "test_count": len(tests),
        "persona_events_count": persona_events,
        "blocking_invariants": [],
        "determinism_match": True,
    }
    (Path(run1_dir) / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))

    assert (Path(run1_dir) / "summary.json").exists()
    s = json.loads((Path(run1_dir) / "summary.json").read_text())
    assert s.get("determinism_match") is True
