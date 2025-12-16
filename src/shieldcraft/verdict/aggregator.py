from __future__ import annotations

import json
import os
import hashlib
from typing import Dict, Any, List


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def compute_implementability(outdir: str = '.selfhost_outputs') -> Dict[str, Any]:
    """Aggregate artifacts and compute a binary IMPLEMENTABLE verdict.

    Rules (strict): IMPLEMENTABLE iff all are true:
      - checklist_sufficiency.json -> 'sufficient' == True
      - spec_coverage.json -> covered_pct >= 0.98
      - checklist_quality.json -> no P0 or P1 items in low_signal_item_ids
      - checklist_execution_plan.json -> cycles/missing_artifacts/priority_violations empty

    The result is persisted to `implementability_verdict.json` in `outdir`.
    """
    artifacts = {}
    def load_json(name: str) -> Any:
        p = os.path.join(outdir, name)
        if os.path.exists(p):
            try:
                return json.load(open(p))
            except Exception:
                return None
        return None

    suff = load_json('checklist_sufficiency.json') or {}
    cov = load_json('spec_coverage.json') or {}
    qual = load_json('checklist_quality.json') or {}
    plan = load_json('checklist_execution_plan.json') or {}

    reasons: List[str] = []

    # sufficiency
    if not suff.get('sufficient'):
        reasons.append('sufficiency_failed')

    # coverage (ignore structural dump units)
    try:
        total_units = int(cov.get('total_units', 0) or 0)
        structural_count = len(cov.get('structural_unit_ids', []) or [])
        adjusted_total = max(0, total_units - structural_count)
        covered_count = int(cov.get('covered_count', 0) or 0)
        adjusted_cov_pct = (covered_count / adjusted_total) if adjusted_total else 1.0
        if adjusted_cov_pct < 0.98:
            reasons.append(f'coverage_below_threshold:{adjusted_cov_pct}')
    except Exception:
        reasons.append('coverage_below_threshold:0.0')

    # quality: ensure no P0/P1 items are low-signal
    low_ids = set(qual.get('summary', {}).get('low_signal_item_ids', []) or [])
    # need to map ids->priority by loading checklist
    checklist = load_json('checklist.json') or {}
    items = checklist.get('items', []) or []
    id_to_pr = {it.get('id'): (it.get('priority') or '').upper() for it in items}
    p0p1_violations = [iid for iid in low_ids if id_to_pr.get(iid, '').startswith('P0') or id_to_pr.get(iid, '').startswith('P1')]
    if p0p1_violations:
        reasons.append('p0p1_low_signal:' + ','.join(sorted(p0p1_violations)))

    # execution plan
    cycles = plan.get('cycles') or {}
    missing_artifacts = plan.get('missing_artifacts') or []
    priority_violations = plan.get('priority_violations') or []
    if cycles:
        reasons.append('execution_cycles')
    if missing_artifacts:
        reasons.append('missing_artifacts')
    if priority_violations:
        reasons.append('priority_violations')

    implementable = (len(reasons) == 0)

    # Proof references: include artifact file SHA256s when present
    proof_refs: Dict[str, str] = {}
    for name in ('checklist_sufficiency.json', 'spec_coverage.json', 'checklist_quality.json', 'checklist_execution_plan.json', 'requirement_completeness.json'):
        p = os.path.join(outdir, name)
        if os.path.exists(p):
            try:
                proof_refs[name] = _sha256_of_file(p)
            except Exception:
                proof_refs[name] = 'unhashable'

    verdict = {
        'implementable': implementable,
        'blocking_reasons': sorted(reasons),
        'proof_references': proof_refs,
    }

    # persist deterministically
    try:
        os.makedirs(outdir, exist_ok=True)
        p = os.path.join(outdir, 'implementability_verdict.json')
        with open(p + '.tmp', 'w', encoding='utf8') as f:
            json.dump(verdict, f, indent=2, sort_keys=True)
        os.replace(p + '.tmp', p)
    except Exception:
        pass

    return verdict
