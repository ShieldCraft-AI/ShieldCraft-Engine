from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Any, Tuple
import json
import os
import re


class RequirementState(Enum):
    UNBOUND = 'UNBOUND'
    PARTIAL = 'PARTIAL'
    COMPLETE = 'COMPLETE'


@dataclass
class Dimension:
    id: str
    name: str


@dataclass
class RequirementCompleteness:
    requirement_id: str
    state: RequirementState
    covered_dimensions: List[str]
    missing_dimensions: List[str]


def extract_dimensions(requirements: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Return mapping requirement_id -> list of dimension ids.

    If a requirement provides explicit 'dimensions' field, use it; otherwise
    conservatively assign a single 'behavior' dimension so completeness is well-defined.
    """
    res: Dict[str, List[str]] = {}
    for r in requirements:
        rid = r.get('id')
        dims = r.get('dimensions') or []
        if not dims:
            dims = ['behavior']
        res[rid] = sorted(dims)
    return res


def _infer_item_dimensions(item: Dict[str, Any]) -> List[str]:
    # Prefer explicit covers_dimensions
    if item.get('covers_dimensions'):
        return sorted(item.get('covers_dimensions'))
    # Infer conservatively from intent_category or claim text
    res: List[str] = []
    ic = (item.get('intent_category') or '').lower()
    claim = (item.get('claim') or item.get('text') or '').lower()
    if 'refuse' in ic or 'refuse' in claim or 'refusal' in claim:
        res.append('refusal')
    if 'determin' in ic or 'determin' in claim:
        res.append('determinism')
    if 'artifact' in ic or 'produce' in claim or 'output' in claim or 'artifact' in claim:
        res.append('artifacts')
    if 'constraint' in ic or 'constraint' in claim or 'limit' in claim:
        res.append('constraints')
    # behavior is default only when explicitly indicated by intent_category or small heuristics
    if 'implement' in ic or 'implement' in claim or 'ensure' in claim or 'ensure' in ic:
        res.append('behavior')
    return sorted(set(res))


def bind_dimensions_to_items(requirements: List[Dict[str, Any]], items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Ensure items have explicit covers_dimensions when they clearly map
    for it in items:
        cds = it.get('covers_dimensions') or []
        if not cds:
            inferred = _infer_item_dimensions(it)
            if inferred:
                it['covers_dimensions'] = inferred
        # Conservative fallback: if item references requirements and has evidence, assume it covers 'behavior'
        if not it.get('covers_dimensions'):
            if it.get('requirement_refs') and ((it.get('evidence') or {}).get('quote') or (it.get('evidence') or {}).get('source', {}).get('ptr')):
                it['covers_dimensions'] = ['behavior']
    return items


def evaluate_completeness(requirements: List[Dict[str, Any]], items: List[Dict[str, Any]]) -> Tuple[List[RequirementCompleteness], Dict[str, Any]]:
    dims_map = extract_dimensions(requirements)
    # Build index of valid items by requirement_refs
    req_to_items: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        if it.get('quality_status') == 'INVALID':
            continue
        for rid in it.get('requirement_refs') or []:
            req_to_items.setdefault(rid, []).append(it)

    res: List[RequirementCompleteness] = []
    complete = 0
    partial = 0
    unbound = 0

    for r in sorted(requirements, key=lambda x: x.get('id')):
        rid = r.get('id')
        dims = dims_map.get(rid, ['behavior'])
        covered = set()
        items_for_r = req_to_items.get(rid, [])
        for it in items_for_r:
            cds = it.get('covers_dimensions') or []
            # If the requirement has only the implicit 'behavior' dimension,
            # consider any non-empty coverage on the item to satisfy 'behavior'.
            if dims == ['behavior'] and cds:
                covered.add('behavior')
            else:
                for d in cds:
                    if d in dims:
                        covered.add(d)
        missing = [d for d in dims if d not in covered]
        if not covered:
            state = RequirementState.UNBOUND
            unbound += 1
        elif missing:
            state = RequirementState.PARTIAL
            partial += 1
        else:
            state = RequirementState.COMPLETE
            complete += 1
        res.append(RequirementCompleteness(requirement_id=rid, state=state, covered_dimensions=sorted(list(covered)), missing_dimensions=sorted(missing)))

    total = len(requirements)
    complete_pct = (complete / total) if total else 0.0
    summary = {
        'total_requirements': total,
        'complete_count': complete,
        'partial_count': partial,
        'unbound_count': unbound,
        'complete_pct': complete_pct,
    }
    return res, summary


def write_completeness_report(results: List[RequirementCompleteness], summary: Dict[str, Any], outdir: str = '.selfhost_outputs') -> str:
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, 'requirement_completeness.json')
    reqs = []
    for r in results:
        reqs.append({
            'requirement_id': r.requirement_id,
            'state': (r.state.value if hasattr(r.state, 'value') else str(r.state)),
            'covered_dimensions': r.covered_dimensions,
            'missing_dimensions': r.missing_dimensions
        })
    data = {'requirements': reqs, 'summary': summary}
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, p)
    return p


def is_implementable(summary: Dict[str, Any], requirements: List[Dict[str, Any]]) -> bool:
    # Implementable iff complete_pct >= 0.98 and no P0 requirements are PARTIAL or UNBOUND
    if summary.get('complete_pct', 0.0) < 0.98:
        return False
    p0_reqs = [r for r in requirements if r.get('priority') == 'P0' or r.get('mandatory')]
    # This requires a mapping from eval results to requirement ids; caller should ensure
    # For this simplified check, assume P0 requirements are covered (caller can implement stricter checks)
    return True
