"""Generate deterministic system health summary for operational audits.

The summary is written to `artifacts/SYSTEM_HEALTH.md` and is deterministic
across runs given the same repository state.
"""
from __future__ import annotations

import os
from typing import List

from shieldcraft.persona import PERSONA_STABLE, PERSONA_COMPLETE, PERSONA_ENTRY_POINTS
from shieldcraft.services.selfhost import ALLOWED_SELFHOST_PREFIXES, ALLOWED_SELFHOST_INPUT_KEYS


def generate_system_health(out_path: str = "artifacts/SYSTEM_HEALTH.md") -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    lines: List[str] = []
    lines.append("# SYSTEM HEALTH — Deterministic Summary")
    lines.append("")
    lines.append("## Persona Subsystem")
    lines.append(f"- STABLE: {PERSONA_STABLE}")
    lines.append(f"- COMPLETE: {PERSONA_COMPLETE}")
    caps = sorted({c for c, n in PERSONA_ENTRY_POINTS})
    lines.append(f"- Entry points: {', '.join(caps)}")

    lines.append("")
    lines.append("## Self-host artifact policy")
    for p in sorted(ALLOWED_SELFHOST_PREFIXES):
        lines.append(f"- allowed_prefix: {p}")
    lines.append("")
    lines.append("## Self-host input keys")
    for k in sorted(ALLOWED_SELFHOST_INPUT_KEYS):
        lines.append(f"- allowed_input_key: {k}")

    lines.append("")
    lines.append("## Notes")
    lines.append("- Deterministic: generated without timestamps")
    lines.append("- Single enforcement paths: persona annotate/veto")
    lines.append("")
    # Stability marker
    try:
        with open("STABLE", encoding='utf-8') as f:
            marker = f.read().strip()
    except (IOError, OSError, ValueError):
        marker = "MISSING"
    lines.append(f"## Stability Marker: {marker}")
    try:
        with open("RELEASE_READY", encoding='utf-8') as f:
            release = f.read().strip()
    except (IOError, OSError, ValueError):
        release = "MISSING"
    lines.append(f"## Release Marker: {release}")

    with open(out_path, "w", encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")


def read_system_health(out_path: str = "artifacts/SYSTEM_HEALTH.md") -> str:
    if not os.path.exists(out_path):
        return ""
    return open(out_path).read()
