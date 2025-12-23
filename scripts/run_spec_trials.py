#!/usr/bin/env python3
"""Run self-host trials across many specs and aggregate factual results.

This tool is resilient: it continues on per-spec failure and records facts-only
results and raw artifacts for later inspection.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _read_engine_version() -> str:
    # Best-effort: read from pyproject.toml if present
    try:
        p = Path(__file__).resolve().parents[1] / "pyproject.toml"
        if p.exists():
            for line in p.read_text().splitlines():
                if line.strip().startswith("version"):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return "unknown"


def _ensure_clean_outputs():
    d = Path(".selfhost_outputs")
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(exist_ok=True)
    return d


def _safe_write(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


def run_trials(
        specs_dir: str,
        schema: str = "src/shieldcraft/dsl/schema/se_dsl.schema.json",
        out_report: str = "spec_trial_report.json",
        raw_artifacts_dir: str = "spec_trial_artifacts"):
    from importlib import import_module
    # local imports that rely on package
    ingest_spec = import_module("shieldcraft.services.spec.ingestion").ingest_spec
    Engine = import_module("shieldcraft.engine").Engine
    try:
        ValidationError = import_module("shieldcraft.services.validator").ValidationError
    except Exception:
        ValidationError = Exception

    specs_root = Path(specs_dir)
    collected: List[Dict[str, Any]] = []

    # Gather files deterministically
    files = [p for p in sorted([p for p in specs_root.rglob("*") if p.is_file()])]

    for idx, fp in enumerate(files):
        entry: Dict[str, Any] = {"spec_path": str(fp), "error_codes": []}
        artifacts_base = Path(raw_artifacts_dir) / f"{idx:04d}_{fp.name}"
        # Clean .selfhost_outputs and ensure clean dir
        try:
            _ensure_clean_outputs()
        except Exception:
            pass

        # Load spec
        try:
            spec = ingest_spec(str(fp))
        except Exception as e:
            entry["error_codes"].append({"type": "ingest_error", "message": str(e)})
            artifacts_base.mkdir(parents=True, exist_ok=True)
            _safe_write(artifacts_base / "errors.json", {"errors": [{"type": "ingest_error", "message": str(e)}]})
            collected.append(entry)
            continue

        # Run engine self-host via API (fresh Engine per spec)
        try:
            engine = Engine(schema)
            result = engine.run_self_host(spec, dry_run=False)
            manifest = result.get("manifest", {}) or {}

            # Capture facts
            entry["conversion_state"] = manifest.get("conversion_state")
            entry["readiness_status"] = (manifest.get("readiness", {}) or {}).get(
                "status") if manifest.get("readiness") else None
            entry["state_reason"] = manifest.get("state_reason")
            entry["conversion_path_next_state"] = (manifest.get("conversion_path") or {}).get(
                "next_state") if manifest.get("conversion_path") else None
            entry["checklist_preview_items"] = manifest.get("checklist_preview_items")
            entry["what_was_produced"] = ["manifest.json", "summary.json"]
            entry["what_was_skipped"] = []

            # Write raw artifacts for later inspection
            artifacts_base.mkdir(parents=True, exist_ok=True)
            _safe_write(artifacts_base / "manifest.json", manifest)
            # Build a minimal summary for facts (status success)
            summary = {
                "status": "success",
                "fingerprint": result.get("fingerprint"),
                "conversion_state": manifest.get("conversion_state"),
                "state_reason": manifest.get("state_reason"),
                "readiness_status": entry["readiness_status"],
            }
            _safe_write(artifacts_base / "summary.json", summary)

            # Capture checklist draft from engine output if present
            try:
                out_dir = Path(result.get("output_dir"))
                # Debug: show output_dir and files for triage
                try:
                    print(f"[SPEC-TRIAL-DEBUG] output_dir={out_dir} exists={out_dir.exists()}")
                    if out_dir.exists():
                        print(f"[SPEC-TRIAL-DEBUG] out_dir files: {[p.name for p in out_dir.iterdir()]}")
                except Exception:
                    pass
                # Check both final emitted checklist and draft checklist for emitted signal
                cd_final = out_dir / "checklist.json"
                cd_draft = out_dir / "checklist_draft.json"
                if cd_final.exists():
                    print(f"[SPEC-TRIAL-DEBUG] entering cd_final branch for {cd_final}")
                    try:
                        txt = cd_final.read_text()
                        try:
                            data = json.loads(txt)
                            print(f"[SPEC-TRIAL-DEBUG] parsed checklist.json items={len(data.get('items', []))}")
                        except Exception as _je:
                            print(f"[SPEC-TRIAL-DEBUG] failed to parse {cd_final}: {_je}; snippet: {txt[:200]!r}")
                            raise
                        entry["checklist_emitted"] = True
                        entry["checklist_item_count"] = len(data.get("items", []))
                        # Copy into artifacts for review (preserve name)
                        _safe_write(artifacts_base / "checklist.json", data)
                    except Exception as _e:
                        import traceback as _tb
                        print(f"[SPEC-TRIAL-DEBUG] exception in cd_final branch: {_e}\n{_tb.format_exc()}")
                        entry["checklist_emitted"] = False
                        entry["checklist_item_count"] = 0
                elif cd_draft.exists():
                    try:
                        data = json.loads(cd_draft.read_text())
                        entry["checklist_emitted"] = True
                        entry["checklist_item_count"] = len(data.get("items", []))
                        _safe_write(artifacts_base / "checklist_draft.json", data)
                    except Exception:
                        entry["checklist_emitted"] = False
                        entry["checklist_item_count"] = 0
                # Optionally compare against baseline if provided via env var
                baseline_dir = os.getenv("SPEC_TRIAL_BASELINE_DIR")
                if baseline_dir:
                    try:
                        base_path = Path(baseline_dir) / fp.name / "checklist_draft.json"
                        if base_path.exists():
                            base = json.loads(base_path.read_text())
                            added = [
                                i for i in data.get(
                                    "items", []) if i.get("id") not in {
                                    b.get("id") for b in base.get(
                                        "items", [])}]
                            removed = [
                                i for i in base.get(
                                    "items", []) if i.get("id") not in {
                                    d.get("id") for d in data.get(
                                        "items", [])}]
                            changed = []
                            base_map = {b.get("id"): b for b in base.get("items", [])}
                            for it in data.get("items", []):
                                bid = it.get("id")
                                if bid in base_map and json.dumps(
                                        it, sort_keys=True) != json.dumps(
                                        base_map[bid], sort_keys=True):
                                    changed.append(it)
                            entry["checklist_diff_added"] = len(added)
                            entry["checklist_diff_removed"] = len(removed)
                            entry["checklist_diff_changed"] = len(changed)
                    except Exception:
                        entry["checklist_diff_added"] = None
                        entry["checklist_diff_removed"] = None
                        entry["checklist_diff_changed"] = None
                # Capture spec feedback when available
                sf = out_dir / "spec_feedback.json"
                if sf.exists():
                    try:
                        fb = json.loads(sf.read_text())
                        entry["remediation_hints_count"] = fb.get("remediation_hints_count")
                        entry["missing_sections"] = fb.get("missing_sections")
                        _safe_write(artifacts_base / "spec_feedback.json", fb)
                    except Exception:
                        entry["remediation_hints_count"] = 0
                        entry["missing_sections"] = []
                # NOTE: Do NOT unset checklist_emitted here if spec_feedback is absent; presence
                # of a checklist is independent of spec_feedback.
            except Exception:
                entry["checklist_emitted"] = False
                entry["checklist_item_count"] = 0

        except ValidationError as e:
            # Deterministic validation error: capture details and continue
            err = e.to_dict() if hasattr(e, "to_dict") else {"message": str(e)}
            entry["error_codes"].append(err.get("code") if isinstance(err, dict) else getattr(e, "code", str(e)))
            # Build a minimal partial manifest mirroring self-host behavior
            manifest = {
                "partial": True,
                "conversion_tier": "convertible",
                "conversion_state": "CONVERTIBLE",
                "state_reason": getattr(e, "code", None),
                "spec_metadata": spec.get("metadata", {}),
            }
            artifacts_base.mkdir(parents=True, exist_ok=True)
            _safe_write(artifacts_base / "errors.json", {"errors": [err]})
            _safe_write(artifacts_base / "manifest.json", manifest)
            # Attempt to produce a checklist draft even when validation fails
            try:
                from shieldcraft.services.ast.builder import ASTBuilder
                from shieldcraft.services.checklist.generator import ChecklistGenerator
                from shieldcraft.services.guidance.checklist import (
                    annotate_items, annotate_items_with_blockers,
                    enrich_with_confidence_and_evidence)
                ast = ASTBuilder().build(spec)
                checklist_obj = ChecklistGenerator().build(
                    spec, ast=ast, dry_run=True, run_test_gate=False,
                    engine=Engine(schema))
                if isinstance(checklist_obj, dict):
                    annotate_items(checklist_obj.get("items", []))
                    annotate_items_with_blockers(
                        checklist_obj.get(
                            "items", []), validation_errors=[
                            getattr(
                                e, "code", None)])
                    try:
                        from shieldcraft.services.guidance.checklist import ensure_item_fields
                        enrich_with_confidence_and_evidence(checklist_obj.get("items", []), spec)
                        ensure_item_fields(checklist_obj.get("items", []))
                    except Exception:
                        pass
                    _safe_write(artifacts_base / "checklist_draft.json",
                                {"items": checklist_obj.get("items", []), "status": "draft"})
                    # Post-write guard
                    try:
                        from shieldcraft.services.guidance.checklist import ensure_item_fields
                        payload = json.load(open(artifacts_base / "checklist_draft.json"))
                        payload["items"] = ensure_item_fields(payload.get("items", []))
                        _safe_write(artifacts_base / "checklist_draft.json", payload)
                    except Exception:
                        pass
                    entry["checklist_emitted"] = True
                    entry["checklist_item_count"] = len(checklist_obj.get("items", []))
                    # Attempt to compute and persist spec_feedback for validation failures
                    try:
                        from shieldcraft.services.guidance.checklist import (
                            annotate_items_with_remediation, build_spec_feedback)
                        items = checklist_obj.get("items", [])
                        annotate_items_with_remediation(items, spec)
                        fb = build_spec_feedback(items, spec)
                        _safe_write(artifacts_base / "spec_feedback.json", fb)
                        entry["remediation_hints_count"] = fb.get("remediation_hints_count")
                        entry["missing_sections"] = fb.get("missing_sections")
                    except Exception:
                        entry["remediation_hints_count"] = 0
                        entry["missing_sections"] = []
                else:
                    entry["checklist_emitted"] = False
                    entry["checklist_item_count"] = 0
            except Exception:
                entry["checklist_emitted"] = False
                entry["checklist_item_count"] = 0
            # Minimal summary
            summary = {"status": "fail", "validity_status": "fail", "errors": [
                err], "conversion_state": manifest.get("conversion_state")}
            _safe_write(artifacts_base / "summary.json", summary)
            entry["conversion_state"] = manifest.get("conversion_state")
            entry["readiness_status"] = "not_evaluated"
            entry["state_reason"] = manifest.get("state_reason")

        except Exception as e:
            # Unexpected: capture type/message and continue
            tb = traceback.format_exc()
            print(f"[SPEC-TRIAL-ERROR] Unexpected exception for {fp}: {type(e).__name__}: {e}")
            print(tb)
            entry["error_codes"].append({"type": type(e).__name__, "message": str(e)})
            artifacts_base.mkdir(parents=True, exist_ok=True)
            _safe_write(artifacts_base / "errors.json",
                        {"errors": [{"type": type(e).__name__, "message": str(e), "traceback": tb}]})
            # Explicitly record missing checklist
            entry["checklist_emitted"] = False
            entry["checklist_item_count"] = 0

        collected.append(entry)
        # Emit debug trace for per-spec results to aid triage when running CLI
        try:
            print(
                f"[SPEC-TRIAL] spec={entry.get('spec_path')} "
                f"checklist_emitted={entry.get('checklist_emitted')} "
                f"items={entry.get('checklist_item_count')}")
        except Exception:
            pass

    # Write aggregate report with run metadata
    report = {
        "metadata": {
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "engine_version": _read_engine_version(),
            "python_version": sys.version.replace("\n", " "),
            "spec_count": len(collected),
        },
        "results": collected,
    }
    _safe_write(Path(out_report), report)

    # Enforce checklist visibility guard: fail run if any spec did not emit checklist
    missing = [r.get("spec_path") for r in collected if not r.get("checklist_emitted")]
    if missing:
        # Debug: print collected entries for triage
        try:
            for r in collected:
                print(
                    f"[SPEC-TRIAL-DEBUG] {r.get('spec_path')} "
                    f"emitted={r.get('checklist_emitted')} "
                    f"items={r.get('checklist_item_count')} "
                    f"errors={r.get('error_codes')}")
        except Exception:
            pass
    if missing:
        raise AssertionError(f"Checklist not emitted for specs: {missing}")

    return str(out_report)


def _cli():
    p = argparse.ArgumentParser()
    p.add_argument("specs_dir")
    p.add_argument("--schema", default="src/shieldcraft/dsl/schema/se_dsl.schema.json")
    p.add_argument("--out", default="spec_trial_report.json")
    p.add_argument("--artifacts", default="spec_trial_artifacts")
    args = p.parse_args()
    run_trials(args.specs_dir, args.schema, args.out, args.artifacts)


if __name__ == "__main__":
    _cli()
