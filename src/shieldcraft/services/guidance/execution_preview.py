"""Deterministic, hypothetical execution preview generator.

Produces a non-executing preview describing what would be generated
and executed if the spec progressed to READY. Always marked hypothetical.
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional, Set


def _artifact_from_item(item: Dict[str, Any]) -> Optional[str]:
    # Prefer explicit artifact_type, fall back to category heuristics
    if not isinstance(item, dict):
        return None
    if item.get("artifact_type"):
        return item.get("artifact_type")
    cat = item.get("category")
    if cat == "bootstrap":
        return "bootstrap_code"
    if cat == "test":
        return "tests"
    if cat == "integration":
        return "integration_tests"
    if cat == "plan":
        return "execution_plan"
    return None


def _stage_from_item(item: Dict[str, Any]) -> Optional[str]:
    if not isinstance(item, dict):
        return None
    cat = item.get("category")
    if cat == "bootstrap":
        return "codegen"
    if cat in ("test", "integration"):
        return "tests"
    if cat == "plan":
        return "plan"
    return None


def _risk_from_readiness(readiness: Optional[Dict[str, Any]]) -> str:
    # Deterministic risk mapping
    if not readiness:
        return "medium"
    rs = readiness.get("readiness_summary") or readiness.get("readiness_summary")
    if not rs:
        # Fallback on summary counts
        rb = readiness.get("results", {})
        blocking = 0
        non_blocking = 0
        for r in rb.values():
            if isinstance(r, dict) and not r.get("ok"):
                if r.get("blocking"):
                    blocking += 1
                else:
                    non_blocking += 1
        if blocking > 0:
            return "high"
        if non_blocking >= 2:
            return "medium"
        return "low"
    if rs.get("blocking_count", 0) > 0:
        return "high"
    if rs.get("non_blocking_count", 0) >= 2:
        return "medium"
    return "low"


def build_execution_preview(conversion_state: Optional[str], checklist_items: Optional[List[Dict[str, Any]]], readiness: Optional[Dict[str, Any]], missing_next: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    """Return execution_preview dict or None.

    - Only eligible for conversion_state in STRUCTURED or VALID.
    - Never emitted for READY.
    - Always mark `hypothetical`: True.
    """
    cur = (conversion_state or "").upper()
    if cur not in ("STRUCTURED", "VALID"):
        return None
    # Do not emit preview for READY
    if cur == "READY":
        return None

    items = checklist_items or []
    artifacts: Set[str] = set()
    stages: Set[str] = set()
    for it in items:
        a = _artifact_from_item(it)
        if a:
            artifacts.add(a)
        s = _stage_from_item(it)
        if s:
            stages.add(s)

    # deterministic ordering
    would_generate = sorted(artifacts)
    would_execute = sorted(stages)

    # would_require: missing readiness conditions (blocking gates) or missing_next codes
    would_require: List[str] = []
    if readiness:
        for g, r in sorted(readiness.get("results", {}).items()):
            if isinstance(r, dict) and not r.get("ok") and r.get("blocking"):
                would_require.append(g)
    if not would_require and missing_next:
        would_require = [i.get("code") or i.get("message") or "unspecified" for i in missing_next]

    risk = _risk_from_readiness(readiness)

    preview = {
        "hypothetical": True,
        "would_generate": would_generate,
        "would_execute": would_execute,
        "would_require": would_require,
        "risk_level": risk,
        "note": "This is a hypothetical preview. No code or execution is performed."
    }
    return preview
