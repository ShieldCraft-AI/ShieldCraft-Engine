"""Emit a deterministic governance/audit bundle from existing summary and manifest.

This module does not recompute any values; it only reads the written
`summary.json` and `manifest.json` and emits a compact `governance_bundle.json`
and an `audit_index.json` containing file hashes and a canonical creation
timestamp derived deterministically from the spec fingerprint.
"""
from __future__ import annotations

import json
import hashlib
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _sha256_hex(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(8192)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _deterministic_timestamp_from_fingerprint(fp: str) -> str:
    # Derive a deterministic but canonical ISO8601 timestamp from the spec fingerprint.
    # Use first 10 hex chars of sha256(fp) as seconds offset from 2000-01-01.
    if not fp:
        return "1970-01-01T00:00:00Z"
    h = hashlib.sha256(fp.encode()).hexdigest()
    secs = int(h[:10], 16) % 2_000_000_000  # keep within reasonable range
    base = datetime(2000, 1, 1, tzinfo=timezone.utc)
    dt = base + timedelta(seconds=secs)
    return dt.isoformat().replace("+00:00", "Z")


def emit_governance_bundle(output_dir: str = ".selfhost_outputs") -> None:
    manifest_path = os.path.join(output_dir, "manifest.json")
    summary_path = os.path.join(output_dir, "summary.json")
    if not os.path.exists(manifest_path) or not os.path.exists(summary_path):
        return

    manifest = _read_json(manifest_path)
    summary = _read_json(summary_path)

    spec_fp = manifest.get("spec_fingerprint") or manifest.get("fingerprint") or summary.get("fingerprint") or None

    # Compose bundle strictly from existing fields (no recomputation)
    bundle: Dict[str, Any] = {
        "bundle_version": "v1",
        "spec_fingerprint": spec_fp,
        "conversion_state": manifest.get("conversion_state") or summary.get("conversion_state"),
        "readiness_status": (manifest.get("readiness", {}).get("status") if manifest.get("readiness") else summary.get("readiness_status")) or None,
        "artifact_contract_summary": manifest.get("artifact_contract_summary") or summary.get("artifact_contract_summary"),
        "conversion_path": summary.get("conversion_path") or manifest.get("conversion_path"),
        "progress_summary": manifest.get("progress_summary") or summary.get("progress_summary"),
        "semantic_strictness_policy": manifest.get("semantic_strictness_policy") or summary.get("semantic_strictness_policy"),
        "governance_enforcements": manifest.get("governance_enforcements") or summary.get("governance_enforcements"),
    }

    # Determinism snapshot references (only if present in manifest or summary)
    det_refs = {}
    prov = manifest.get("provenance") or {}
    if prov.get("snapshot_hash"):
        det_refs["snapshot_hash"] = prov.get("snapshot_hash")
    # Include any determinism hints found in summary/manifest
    if manifest.get("determinism_ref"):
        det_refs["determinism_ref"] = manifest.get("determinism_ref")
    if det_refs:
        bundle["determinism_references"] = det_refs

    # Write bundle file deterministically
    bundle_path = os.path.join(output_dir, "governance_bundle.json")
    with open(bundle_path, "w", encoding='utf-8') as f:
        json.dump(bundle, f, indent=2, sort_keys=True)

    # Audit index: list included files and their hashes, with a canonical creation timestamp
    included = ["manifest.json", "summary.json", "governance_bundle.json"]
    entries: List[Dict[str, str]] = []
    for name in included:
        p = os.path.join(output_dir, name)
        if os.path.exists(p):
            entries.append({"file": name, "sha256": _sha256_hex(p)})

    creation_ts = _deterministic_timestamp_from_fingerprint(spec_fp) if spec_fp else "1970-01-01T00:00:00Z"
    audit_index = {"bundle_version": "v1", "creation_timestamp": creation_ts, "files": entries}

    audit_path = os.path.join(output_dir, "audit_index.json")
    with open(audit_path, "w", encoding='utf-8') as f:
        json.dump(audit_index, f, indent=2, sort_keys=True)
