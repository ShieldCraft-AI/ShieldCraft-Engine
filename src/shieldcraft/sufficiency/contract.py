from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SufficiencyContract:
    """Formal sufficiency contract definitions."""

    COMPLETE_PCT_THRESHOLD: float = 0.98


def is_priority_p0_or_p1(req: Dict[str, Any]) -> bool:
    p = (req.get('priority') or '').upper()
    if p.startswith('P') and len(p) >= 2 and p[1].isdigit():
        try:
            v = int(p[1])
            return v in (0, 1)
        except Exception:
            pass
    # Legacy 'mandatory' support
    if req.get('mandatory'):
        return True
    return False
