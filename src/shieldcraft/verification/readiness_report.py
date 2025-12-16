"""Produce human-readable readiness reports from evaluator outputs."""
from typing import Dict, Any


def render_readiness(report: Dict[str, Any]) -> str:
    lines = []
    ok = report.get("ok", False)
    lines.append(f"SE Readiness: {'OK' if ok else 'NOT READY'}")
    lines.append("")
    results = report.get("results", {})
    for gate, res in sorted(results.items()):
        status = "PASS" if res.get("ok") else "FAIL"
        lines.append(f"- {gate}: {status}")
        if not res.get("ok"):
            reason = res.get("reason")
            lines.append(f"    Reason: {reason}")
    return "\n".join(lines)
