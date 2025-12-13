#!/usr/bin/env python3
"""
Run the ShieldCraft generator (engine + codegen) and save deterministic artifacts for comparison.
Usage: python scripts/run_generator_verify.py --label run1
"""
import argparse
import json
import os
import hashlib
from pathlib import Path
import sys

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shieldcraft.engine import Engine
from shieldcraft.util.json_canonicalizer import canonicalize
from shieldcraft.services.artifacts.lineage import bundle as build_lineage
from shieldcraft.services.spec.fingerprint import compute_spec_fingerprint


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def run_and_capture(label: str, spec_path: str = "spec/se_dsl_v1.spec.json", schema_path: str = "spec/schemas/se_dsl_v1.schema.json"):
    artifacts_dir = Path("artifacts/determinism") / label
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    engine = Engine(schema_path)

    # Ensure spec has canonical dsl_version at top-level; if not, write a temp spec file
    with open(spec_path) as f:
        original_spec = json.load(f)

    temp_spec_path = spec_path
    if original_spec.get("dsl_version") != "canonical_v1_frozen":
        tmp_dir = artifacts_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_spec_file = tmp_dir / "spec_with_dsl.json"
        original_spec["dsl_version"] = "canonical_v1_frozen"
        tmp_spec_file.write_text(json.dumps(original_spec, indent=2))
        temp_spec_path = str(tmp_spec_file)

    # Run engine pipeline (no side-effects expected from run())
    result = engine.run(temp_spec_path)

    spec = result.get("spec", {})
    ast = result.get("ast")
    checklist = result.get("checklist")
    # Normalize checklist to either list or dict
    if isinstance(checklist, dict) and "items" in checklist:
        checklist_items = checklist["items"]
    else:
        checklist_items = checklist or []
    plan = result.get("plan")

    # Use codegen dry_run to avoid writing files
    outputs_preview = engine.codegen.run(checklist_items, dry_run=True)

    # Normalize outputs list
    if isinstance(outputs_preview, dict) and "outputs" in outputs_preview:
        preview_list = outputs_preview["outputs"]
    else:
        preview_list = outputs_preview

    # Save preview outputs and compute hashes
    content_hashes = []
    outputs_dir = artifacts_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    for entry in preview_list:
        # entry is {'path','content','preview','content_hash'} depending on run
        path = entry.get("path") or entry.get("output_path") or entry.get("id") or "unknown"
        content = entry.get("content") or entry.get("preview") or ""
        # canonical path for local storage
        safe_path = str(path).lstrip("./")
        out_path = outputs_dir / safe_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content)
        h = sha256_text(content)
        content_hashes.append((safe_path, h))

    # Save lockfile copy
    lockfile_path = Path("generators/lockfile.json")
    if lockfile_path.exists():
        with open(lockfile_path) as f:
            lockfile_content = f.read()
        (artifacts_dir / "generators_lockfile.json").write_text(lockfile_content)
        lockfile_hash = sha256_text(lockfile_content)
    else:
        lockfile_hash = "missing"

    # Compute aggregated code fingerprint
    sorted_hashes = sorted(content_hashes, key=lambda x: x[0])
    aggregate = "".join([f"{p}:{h}" for p, h in sorted_hashes])
    code_fp = hashlib.sha256(aggregate.encode()).hexdigest()

    # Compute spec and items fingerprints
    spec_fp = compute_spec_fingerprint(spec)
    # items fingerprint from checklist (string canonicalized)
    if isinstance(checklist, dict):
        items_list = checklist.get("items", [])
    else:
        items_list = checklist
    items_fp = hashlib.sha256(canonicalize(json.dumps(items_list)).encode()).hexdigest()
    plan_fp = hashlib.sha256(canonicalize(json.dumps(plan)).encode()).hexdigest() if plan is not None else ""

    lineage = build_lineage(spec_fp, items_fp, plan_fp, code_fp)
    lineage_signature = lineage.get("lineage_hash")

    # Save summary
    summary = {
        "spec_fp": spec_fp,
        "items_fp": items_fp,
        "plan_fp": plan_fp,
        "code_fp": code_fp,
        "code_hashes": sorted_hashes,
        "codegen_bundle_hash": outputs_preview.get("codegen_bundle_hash") if isinstance(outputs_preview, dict) else None,
        "lockfile_hash": lockfile_hash,
        "lineage_signature": lineage_signature
    }
    with open(artifacts_dir / "run.summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)

    print(f"Run '{label}' completed: {len(sorted_hashes)} outputs, code_fp={code_fp}")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run", help="Label for this run (used to create artifacts/determinism/<label>)")
    args = parser.parse_args()

    run_and_capture(args.label)


if __name__ == "__main__":
    main()
