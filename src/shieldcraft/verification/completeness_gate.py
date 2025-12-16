"""Completeness gate: ensure all MUST requirements are implemented at P0/P1.

Exports:
 - evaluate_completeness(requirements, checklist_items) -> report dict
"""
from __future__ import annotations

import json
import os
from typing import List, Dict, Any


def evaluate_completeness(requirements: List[Dict[str, Any]], checklist_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    musts = [r for r in requirements if r.get('modality') == 'MUST']
    total_must = len(musts)
    uncovered = []
    weak = []
    covered = []

    for r in musts:
        rid = r.get('id')
        ptr = r.get('ptr')
        found = []
        for it in checklist_items:
            ev = it.get('evidence') or {}
            src = ev.get('source') or {}
            iptr = src.get('ptr')
            eh = ev.get('source_excerpt_hash')
            # pointer match or excerpt hash
            if iptr and (iptr == ptr or iptr.startswith(ptr.rstrip('/') + '/')):
                found.append(it)
                continue
            if eh and eh == r.get('excerpt_hash'):
                found.append(it)
                continue
        if not found:
            uncovered.append({'id': rid, 'text': r.get('text'), 'ptr': ptr})
        else:
            # check if any found items have priority P0/P1 and confidence not low
            ok = any((it.get('priority') in ('P0', 'P1')) and ((it.get('confidence') or '').lower() != 'low') for it in found)
            covered.append({'id': rid, 'ok': ok, 'found': [it.get('id') for it in found]})
            if not ok:
                weak.append({'id': rid, 'text': r.get('text'), 'ptr': ptr, 'found': [it.get('id') for it in found]})

    report = {
        'total_must': total_must,
        'covered_must': len([c for c in covered if c['ok']]),
        'uncovered_must': uncovered,
        'weak_must': weak,
        'complete': (len(uncovered) == 0 and len(weak) == 0),
    }
    # Also write a compatibility-layer field for older tests
    report['uncovered'] = uncovered
    return report


def write_completeness_report(report: Dict[str, Any], outdir: str = '.selfhost_outputs') -> str:
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, 'completeness_report.json')
    with open(p, 'w', encoding='utf8') as f:
        json.dump(report, f, indent=2)
    return p
