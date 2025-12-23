from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import json
import os


@dataclass
class SufficiencyResult:
    ok: bool
    mandatory_total: int
    mandatory_full: int
    mandatory_missing: int
    mandatory_partial: int
    missing_requirements: List[str]
    partial_requirements: List[str]


def evaluate_sufficiency(requirements: List[Dict[str, Any]], covers: List[Any],
                         reachable_items: List[str] | None = None) -> SufficiencyResult:
    """Evaluate checklist sufficiency.

    A checklist is sufficient iff every mandatory requirement has FULL coverage.
    """
    # Build index of coverage by requirement id
    cov_by_id = {c.requirement_id: c for c in covers}

    # Support multiple shapes: prefer explicit boolean 'mandatory', else check modality/type/level markers
    def _is_mandatory(r: Dict[str, Any]) -> bool:
        if r.get('mandatory'):
            return True
        if str(r.get('modality') or '').upper() == 'MUST':
            return True
        if str(r.get('type') or '').upper() == 'MUST':
            return True
        if str(r.get('level') or '').upper() == 'MUST':
            return True
        return False

    mandatory_ids = [r.get('id') for r in requirements if _is_mandatory(r)]
    mandatory_total = len(mandatory_ids)
    mandatory_full = 0
    mandatory_missing = 0
    mandatory_partial = 0
    missing = []
    partial = []

    for rid in sorted(mandatory_ids):
        c = cov_by_id.get(rid)
        if c is None:
            mandatory_missing += 1
            missing.append(rid)
            continue
        # Check reachability: if reachable_items provided, require at least one coverage item in reachable set
        covered_ids = c.checklist_item_ids or []
        if reachable_items is not None:
            if not any(i in reachable_items for i in covered_ids):
                # coverage exists but items not reachable -> treat as partial/orphan
                mandatory_partial += 1
                partial.append(rid)
                continue
        if c.coverage_status.name == 'FULL':
            mandatory_full += 1
        elif c.coverage_status.name == 'PARTIAL':
            mandatory_partial += 1
            partial.append(rid)
        else:
            mandatory_missing += 1
            missing.append(rid)

    # Require at least one mandatory requirement and all must be FULL
    ok = (mandatory_total > 0) and (mandatory_missing == 0 and mandatory_partial == 0)

    return SufficiencyResult(
        ok=ok,
        mandatory_total=mandatory_total,
        mandatory_full=mandatory_full,
        mandatory_missing=mandatory_missing,
        mandatory_partial=mandatory_partial,
        missing_requirements=sorted(missing),
        partial_requirements=sorted(partial),
    )


def write_sufficiency_report(res: SufficiencyResult, outdir: str = '.selfhost_outputs') -> str:
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, 'sufficiency.json')
    data = asdict(res)
    # convert lists to stable sorted lists
    data['missing_requirements'] = sorted(data.get('missing_requirements') or [])
    data['partial_requirements'] = sorted(data.get('partial_requirements') or [])
    with open(p, 'w', encoding='utf8') as f:
        json.dump({'sufficiency': data}, f, indent=2, sort_keys=True)
    return p
