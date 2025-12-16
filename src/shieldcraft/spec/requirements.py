"""Canonical requirement model and binding utilities.

Provides deterministic extraction wrapper and item binding utilities.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import List, Dict, Any

try:
    from shieldcraft.interpretation.requirements import extract_requirements as _interp_extract
except Exception:
    _interp_extract = None


def _short(h: str) -> str:
    return h[:12]


def extract_requirements(spec_text: str) -> List[Dict[str, Any]]:
    """Canonicalize requirements extracted from raw text.

    Returns list of dicts: {id, level, text, ptr, hash}
    Deterministic ordering by ptr then hash.
    """
    if _interp_extract is None:
        return []
    raw = _interp_extract(spec_text)
    out = []
    for r in raw:
        rid = r.get('id')
        level = r.get('modality')
        text = r.get('text')
        ptr = r.get('ptr')
        h = r.get('excerpt_hash') or _short(hashlib.sha256((text or '').lower().encode()).hexdigest())
        out.append({'id': rid, 'level': level, 'text': text, 'ptr': ptr, 'hash': h, 'line': r.get('line')})
    # stable ordering
    out = sorted(out, key=lambda x: (x.get('ptr') or '', x.get('hash') or ''))
    return out


def persist_requirements(reqs: List[Dict[str, Any]], outdir: str = '.selfhost_outputs') -> str:
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, 'requirements.json')
    with open(p, 'w', encoding='utf8') as f:
        json.dump({'requirements': reqs}, f, indent=2, sort_keys=True)
    return p


def bind_requirements_to_items(reqs: List[Dict[str, Any]], items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add `requirement_refs` to checklist items by ptr overlap or excerpt hash.

    Returns the mutated items list.
    """
    # Build index by ptr and hash
    req_by_ptr = {}
    req_by_hash = {}
    for r in reqs:
        req_by_ptr.setdefault(r.get('ptr'), []).append(r)
        req_by_hash.setdefault(r.get('hash'), []).append(r)

    for it in items:
        refs = set()
        ev = it.get('evidence') or {}
        src = ev.get('source') or {}
        iptr = src.get('ptr')
        ihash = ev.get('source_excerpt_hash')
        # ptr exact or child
        if iptr:
            for p, rlist in req_by_ptr.items():
                if iptr == p or iptr.startswith((p or '').rstrip('/') + '/'):
                    for r in rlist:
                        refs.add(r['id'])
        # excerpt hash
        if ihash and ihash in req_by_hash:
            for r in req_by_hash[ihash]:
                refs.add(r['id'])
        if refs:
            it['requirement_refs'] = sorted(list(refs))
        else:
            it.setdefault('requirement_refs', [])
    return items
