"""Deterministic checklist quality scoring.

Score range: 0–100 (higher is better). Factors:
- number of Tier A missing/blocker items
- number of synthesized defaults (Tier A/B)
- number of insufficiency diagnostics
- item coverage (normalized by total items) not implemented here (kept simple)
"""
from typing import List, Dict, Any


def compute_checklist_quality(items: List[Dict[str, Any]],
                              synthesized_count: int = 0, insufficiency_count: int = 0) -> int:
    score = 100
    # Count Tier A blocker items deterministically
    tier_a_blockers = 0
    for it in items:
        meta = it.get('meta') or {}
        if meta.get('tier') == 'A' or (it.get('text') or '').startswith('SPEC MISSING'):
            tier_a_blockers += 1
    # Penalties
    score -= min(90, 30 * tier_a_blockers)  # heavy penalty per blocker
    score -= min(50, 10 * synthesized_count)
    score -= min(50, 5 * insufficiency_count)

    # Clamp
    if score < 0:
        score = 0
    if score > 100:
        score = 100
    return int(score)
