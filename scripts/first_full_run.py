import os
import json
import yaml
import shutil
from pathlib import Path

from shieldcraft.engine import Engine
from shieldcraft.util.json_canonicalizer import canonicalize

OUT_DIR = Path("artifacts/first_full_run")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SPEC_YAML = Path("spec/test_spec.yml")
SPEC_JSON = OUT_DIR / "spec.json"

# Ensure persona enabled and TAC enforcement disabled
os.environ.pop("SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT", None)
os.environ["SHIELDCRAFT_PERSONA_ENABLED"] = "1"

# Load YAML spec
with open(SPEC_YAML) as f:
    spec = yaml.safe_load(f)

# Canonicalize and write JSON spec
spec_canon = canonicalize(spec)
SPEC_JSON.write_text(spec_canon)

# Helper to run engine and collect artifacts


def run_once(tag: str):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    engine.persona_enabled = True

    # Clear transient observability files to avoid cross-run bleed
    exec_dir = Path("artifacts")
    for fname in [
        "execution_state_v1.json",
        "persona_annotations_v1.json",
        "persona_events_v1.json",
            "persona_events_v1.hash"]:
        p = exec_dir / fname
        if p.exists():
            p.unlink()

    # Run main pipeline (validation + checklist + plan)
    res = engine.run(str(SPEC_JSON))

    run_dir = OUT_DIR / tag
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)

    # Write spec, checklist, plan
    (run_dir / "generated_spec.json").write_text(json.dumps(res.get("spec", {}), indent=2, sort_keys=True))
    (run_dir / "generated_checklist.json").write_text(json.dumps(res.get("checklist", {}), indent=2, sort_keys=True))
    (run_dir / "generated_plan.json").write_text(json.dumps(res.get("plan", {}), indent=2, sort_keys=True))

    # Determinism snapshot
    det = res.get("checklist", {}).get("_determinism")
    if det is not None:
        (run_dir / "determinism_snapshot.json").write_text(json.dumps(det, indent=2, sort_keys=True))

    # Generate code (dry-run)
    outputs = engine.generate_code(str(SPEC_JSON), dry_run=True)
    outs = outputs.get("outputs") if isinstance(outputs, dict) and "outputs" in outputs else outputs
    code_dir = run_dir / "generated"
    code_dir.mkdir()
    for idx, o in enumerate(outs):
        if isinstance(o, dict):
            path = code_dir / o.get("path", f"output_{idx}.txt")
            path.write_text(o.get("content", ""))
        else:
            # legacy string output
            path = code_dir / f"output_{idx}.txt"
            path.write_text(str(o))

    # Collect test-like files
    tests = []
    for f in code_dir.rglob("*"):
        if f.is_file() and ("test" in f.name or "tests" in f.parts):
            tests.append(str(f.relative_to(run_dir)))
    (run_dir / "generated_test_plan.json").write_text(json.dumps({"tests": tests}, indent=2, sort_keys=True))

    # Copy persona events if emitted
    events_src = Path("artifacts/persona_events_v1.json")
    if events_src.exists():
        shutil.copy(events_src, run_dir / "persona_events_v1.json")
        hash_src = Path("artifacts/persona_events_v1.hash")
        if hash_src.exists():
            shutil.copy(hash_src, run_dir / "persona_events_v1.hash")

    # Return list of produced files
    produced = list(run_dir.rglob("**/*"))
    produced = [str(p.relative_to(run_dir)) for p in produced if p.is_file()]
    return run_dir, produced


# First run
run1_dir, run1_files = run_once("run1")
# Second run for determinism
run2_dir, run2_files = run_once("run2")

# Compare files
mismatches = []
for f in sorted(set(run1_files) | set(run2_files)):
    p1 = run1_dir / f
    p2 = run2_dir / f
    if not p1.exists() or not p2.exists():
        mismatches.append({"file": f, "reason": "missing_in_one_run"})
        continue
    b1 = p1.read_bytes()
    b2 = p2.read_bytes()
    if b1 != b2:
        mismatches.append({"file": f, "reason": "content_mismatch"})

# Summarize
summary = {
    "artifact_counts": {"run1": len(run1_files), "run2": len(run2_files)},
    "checklist_size": len(json.loads((run1_dir / "generated_checklist.json").read_text()).get("items", [])),
    "checklist_categories": {},
    "test_surface_size": len(json.loads((run1_dir / "generated_test_plan.json").read_text()).get("tests", [])),
    "persona_participation": 0,
    "mismatches": mismatches,
}
# compute checklist categories
cl = json.loads((run1_dir / "generated_checklist.json").read_text()).get("items", [])
cats = {}
for it in cl:
    c = it.get("category") or "unknown"
    cats[c] = cats.get(c, 0) + 1
summary["checklist_categories"] = cats
# persona participation
pe = run1_dir / "persona_events_v1.json"
if pe.exists():
    summary["persona_participation"] = len(json.loads(pe.read_text()))

# Write summary
(run1_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
print(json.dumps(summary, indent=2))

# Exit with non-zero if mismatches exist
if mismatches:
    raise SystemExit(2)
else:
    raise SystemExit(0)
