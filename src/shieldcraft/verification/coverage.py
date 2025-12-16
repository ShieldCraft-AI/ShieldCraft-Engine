"""Coverage mapping utilities for requirements -> checklist items.

Functions:
 - map_requirements_to_checklist(requirements, checklist_items) -> dict with covered/uncovered/weakly_covered
 - write_sufficiency_report(report, outdir='.selfhost_outputs')

Coverage rule: a requirement is COVERED if any checklist item:
 - has evidence.source.ptr equal to req.ptr or is a child of req.ptr
 - OR evidence.source_excerpt_hash equals req['hash']
 - OR evidence.quote token overlap / req token count >= 0.6

Weak coverage: coverage provided only by P2 items or by items with "low" confidence.
"""
from __future__ import annotations

import json
import os
import re
from typing import List, Dict, Any, Tuple


def _tokenize(s: str):
    return re.findall(r"[a-z0-9]+", (s or '').lower())


def _overlap_ratio(req_norm: str, quote: str) -> float:
    req_toks = _tokenize(req_norm)
    if not req_toks:
        return 0.0
    quote_toks = set(_tokenize(quote))
    overlap = len(set(req_toks) & quote_toks)
    return overlap / len(req_toks)


def _item_covers_req(item: Dict[str, Any], req: Dict[str, Any]) -> Tuple[bool, str]:
    ev = item.get('evidence') or {}
    source = ev.get('source') or {}
    ptr = source.get('ptr') or ''
    # ptr rule
    if ptr and (ptr == req.get('ptr') or ptr.startswith(req.get('ptr', '').rstrip('/') + '/')):
        return True, 'ptr'
    # excerpt hash
    if ev.get('source_excerpt_hash') and ev.get('source_excerpt_hash') == req.get('hash'):
        return True, 'excerpt_hash'
    # token overlap rule
    quote = ev.get('quote') or ''
    ratio = _overlap_ratio(req.get('norm') or req.get('text', ''), quote)
    if ratio >= 0.6:
        return True, 'overlap'
    return False, ''


def map_requirements_to_checklist(requirements: List[Dict[str, Any]], checklist_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    covered = []
    uncovered = []
    weakly_covered = []
    mapping = {}

    for req in requirements:
        req_id = req.get('id')
        mapping[req_id] = []
        req_covered = False
        req_weak = False
        for it in checklist_items:
            ok, rule = _item_covers_req(it, req)
            if not ok:
                continue
            req_covered = True
            mapping[req_id].append({'item_id': it.get('id'), 'rule': rule})
            # weak coverage if priority P2 or confidence low
            if (it.get('priority') == 'P2') or ((it.get('confidence') or '').lower() == 'low'):
                req_weak = True

        if not req_covered:
            uncovered.append({'id': req_id, 'text': req.get('text'), 'ptr': req.get('ptr')})
        else:
            covered.append({'id': req_id, 'text': req.get('text'), 'ptr': req.get('ptr'), 'weak': req_weak})
            if req_weak:
                weakly_covered.append({'id': req_id, 'text': req.get('text'), 'ptr': req.get('ptr')})

    return {
        'mapping': mapping,
        'covered': covered,
        'uncovered': uncovered,
        'weakly_covered': weakly_covered,
    }


def write_sufficiency_report(report: Dict[str, Any], outdir: str = '.selfhost_outputs') -> str:
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, 'sufficiency_report.json')
    with open(p, 'w', encoding='utf8') as f:
        json.dump(report, f, indent=2)
    return p
