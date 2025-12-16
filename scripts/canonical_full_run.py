import os
import json
import shutil
from pathlib import Path

from shieldcraft.engine import Engine
from shieldcraft.util.json_canonicalizer import canonicalize

OUT_DIR = Path("artifacts/canonical_full_run")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SPEC_JSON = Path("spec/se_dsl_v1.spec.json")

# Ensure persona enabled and TAC enforcement disabled for this run
os.environ.pop("SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT", None)
os.environ["SHIELDCRAFT_PERSONA_ENABLED"] = "1"
os.environ["SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY"] = "1"


def run_once(tag: str):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True

    run_dir = OUT_DIR / tag
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)

    # Clear persona/exec state
    exec_dir = Path("artifacts")
    for fname in ["execution_state_v1.json", "persona_annotations_v1.json", "persona_events_v1.json", "persona_events_v1.hash"]:
        p = exec_dir / fname
        if p.exists():
            p.unlink()

    # Load canonical spec
    with open(SPEC_JSON) as f:
        spec = json.load(f)

    # Run self-host dry-run; request preview to be written into run_dir/preview.json
    preview_path = run_dir / "preview.json"
    res = engine.run_self_host(spec, dry_run=True, emit_preview=str(preview_path))

    # Save spec and checklist preview
    (run_dir / "generated_spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True))
    # preview contains `checklist`: list of items
    (run_dir / "generated_checklist.json").write_text(json.dumps(res.get("checklist", []), indent=2, sort_keys=True))

    # Derive test plan by simple heuristic: any generated module with 'test' in name
    tests = []
    for o in res.get("outputs", []):
        p = o.get("path", "")
        if "test" in p or p.endswith("_test.py"):
            tests.append(p)
    (run_dir / "generated_test_plan.json").write_text(json.dumps({"tests": tests}, indent=2, sort_keys=True))

    # Determinism snapshot: try to extract `_determinism` from the original checklist (engine stores elsewhere)
    # If not present, attempt to reconstruct via canonicalized preview
    try:
        det = res.get("manifest", {})
        (run_dir / "determinism_snapshot.json").write_text(json.dumps(det, indent=2, sort_keys=True))
    except Exception:
        pass

    # Copy persona events if produced
    events_src = Path("artifacts/persona_events_v1.json")
    if events_src.exists():
        shutil.copy(events_src, run_dir / "persona_events_v1.json")
        hash_src = Path("artifacts/persona_events_v1.hash")
        if hash_src.exists():
            shutil.copy(hash_src, run_dir / "persona_events_v1.hash")

    # Save full preview if present
    # preview was emitted directly to preview_path via `emit_preview`
    # no additional copy needed

    # Produce a canonical digest of the preview for determinism check
    preview_payload = preview_path.read_text() if preview_path.exists() else json.dumps(res, sort_keys=True)
    digest = canonicalize(json.loads(preview_payload))
    (run_dir / "canonical_preview.json").write_text(digest)

    produced = [str(p.relative_to(run_dir)) for p in run_dir.rglob("**/*") if p.is_file()]
    return run_dir, produced

# Run twice
def main():
    run1_dir, run1_files = run_once("run1")
    run2_dir, run2_files = run_once("run2")

    # Compare canonical preview digests
    p1 = (run1_dir / "canonical_preview.json").read_text()
    p2 = (run2_dir / "canonical_preview.json").read_text()
    mismatch = p1 != p2

    # Gather summary fields
    clist = json.loads((run1_dir / "generated_checklist.json").read_text())
    checklist_item_count = len(clist) if isinstance(clist, list) else 0

    tests = json.loads((run1_dir / "generated_test_plan.json").read_text()).get("tests", [])

    persona_events = 0
    pe = run1_dir / "persona_events_v1.json"
    if pe.exists():
        persona_events = len(json.loads(pe.read_text()))

    # Blocking invariants: not enforced (TAC opt-in); record empty list
    blocking_invariants = []

    summary = {
        "checklist_item_count": checklist_item_count,
        "test_count": len(tests),
        "persona_events_count": persona_events,
        "blocking_invariants": blocking_invariants,
        "determinism_match": not mismatch,
    }

    # Write summary
    (run1_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2))

    return 0 if not mismatch else 2


if __name__ == "__main__":
    import sys
    sys.exit(main())
