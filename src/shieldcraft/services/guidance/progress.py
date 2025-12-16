"""Progress tracking: persist last state and compute progress deltas.

Storage: products/{product_id}/last_state.json (deterministic per product)
"""
from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional, List


STATE_ORDER = ["ACCEPTED", "CONVERTIBLE", "STRUCTURED", "VALID", "READY"]


def _state_index(s: Optional[str]) -> int:
    if not s:
        return -1
    try:
        return STATE_ORDER.index(s)
    except ValueError:
        return -1


def _path_for(product_id: str) -> str:
    return os.path.join("products", product_id, "last_state.json")


def load_last_state(product_id: str) -> Optional[Dict[str, Any]]:
    p = _path_for(product_id)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


def persist_last_state(product_id: str, fingerprint: str, conversion_state: str, readiness_status: str) -> None:
    d = {"fingerprint": fingerprint, "conversion_state": conversion_state, "readiness_status": readiness_status}
    p = _path_for(product_id)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    # Atomic write
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=2, sort_keys=True)
    os.replace(tmp, p)


def compute_progress_summary(prev: Optional[Dict[str, Any]], current_state: Optional[str], current_readiness_status: Optional[str], missing_next: Optional[List[Dict[str, Any]]], readiness_results: Optional[Dict[str, Any]], current_fingerprint: Optional[str] = None) -> Dict[str, Any]:
    prev_state = prev.get("conversion_state") if prev else None
    prev_readiness = prev.get("readiness_status") if prev else None
    prev_fp = prev.get("fingerprint") if prev else None
    cur_state = current_state
    cur_readiness = current_readiness_status or (readiness_results.get("status") if readiness_results else None)

    # Baseline validity check: only use prev if fingerprints match and prev indicates a successful prior run
    valid_baseline = False
    if prev and current_fingerprint and prev_fp == current_fingerprint and prev_readiness == "pass":
        valid_baseline = True

    out: Dict[str, Any] = {"previous_state": (prev if valid_baseline else None), "current_state": cur_state, "delta": None, "reasons": []}

    # Treat as first observation when baseline is not valid
    if not valid_baseline:
        out["delta"] = "initial"
        reasons = []
        if missing_next:
            reasons.extend([i.get("code") or i.get("message") for i in missing_next])
        if readiness_results:
            for g, r in sorted(readiness_results.get("results", {}).items()):
                if isinstance(r, dict) and not r.get("ok"):
                    reasons.append(g)
        out["reasons"] = reasons
        return out

    # Compare conversion states
    prev_idx = _state_index(prev_state)
    cur_idx = _state_index(cur_state)

    # If conversion state changed
    if cur_idx > prev_idx:
        out["delta"] = "advanced"
    elif cur_idx < prev_idx:
        out["delta"] = "regressed"
    else:
        # Same conversion level; inspect readiness changes
        pr = prev_readiness
        cr = cur_readiness
        if pr == "pass" and cr == "fail":
            out["delta"] = "regressed"
        elif pr == "fail" and cr == "pass":
            out["delta"] = "advanced"
        else:
            out["delta"] = "unchanged"

    reasons: List[str] = []
    # For regressions, provide explicit reasons derived from current missing_next and failing readiness gates
    if out["delta"] == "regressed":
        if missing_next:
            reasons.extend([i.get("code") or i.get("message") for i in missing_next])
        if readiness_results:
            for g, r in sorted(readiness_results.get("results", {}).items()):
                if isinstance(r, dict) and not r.get("ok"):
                    # include explanation when present
                    rc = r.get("reason")
                    reasons.append(f"{g}:{rc}" if rc else g)
    elif out["delta"] == "unchanged":
        # Explicitly say why it's unchanged
        if missing_next:
            reasons.append("missing:" + ",".join([i.get("code") or "unspecified" for i in missing_next]))
        elif readiness_results:
            failed = [g for g, r in readiness_results.get("results", {}).items() if isinstance(r, dict) and not r.get("ok")]
            if failed:
                reasons.append("failing_gates:" + ",".join(sorted(failed)))
            else:
                reasons.append("no_change_detected")
    elif out["delta"] == "advanced":
        # Explain what improved
        if prev_state and cur_state:
            reasons.append(f"progressed:{prev_state}->{cur_state}")
        if prev_readiness and cur_readiness and prev_readiness != cur_readiness:
            reasons.append(f"readiness:{prev_readiness}->{cur_readiness}")

    out["reasons"] = reasons
    return out
