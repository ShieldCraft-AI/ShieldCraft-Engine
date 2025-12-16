from __future__ import annotations

from typing import Dict, Any, List
import json
import os
import hashlib

from shieldcraft.coverage.units import build_units_from_spec


def _tokenize(s: str):
    import re
    return re.findall(r"[a-z0-9]+", s.lower())


def bind_units_to_items(units: List[Dict[str, Any]], items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Initialize covers_units
    for it in items:
        it['covers_units'] = sorted(list(set(it.get('covers_units') or [])))

    for u in units:
        uid = u.get('id')
        uptr = u.get('ptr') or ''
        utext = (u.get('text') or '')
        u_tokens = set(_tokenize(utext))
        for it in items:
            matched = False
            # explicit ptr match
            iptr = it.get('ptr') or ''
            if iptr and (iptr == uptr or iptr.startswith(uptr.rstrip('/') + '/')):
                matched = True
            # evidence quote overlap
            ev = it.get('evidence') or {}
            quote = ev.get('quote') or ''
            if not matched and quote:
                overlap = len(u_tokens & set(_tokenize(quote)))
                # requirements tend to be short; allow a smaller absolute overlap threshold
                # but also require a reasonable fraction of the unit tokens to match to
                # avoid accidental matches with JSON-like dumps.
                if (u.get('kind') or '') == 'requirement':
                    thresh = max(2, int(len(u_tokens) * 0.4))
                else:
                    thresh = 5
                if overlap >= thresh:
                    matched = True
            # excerpt hash
            if not matched and quote:
                h = hashlib.sha256(utext.lower().encode()).hexdigest()[:12]
                if h == (ev.get('source_excerpt_hash') or ''):
                    matched = True
            if matched:
                lst = set(it.get('covers_units') or [])
                lst.add(uid)
                it['covers_units'] = sorted(lst)

    return items


def evaluate_spec_coverage(spec: Dict[str, Any], items: List[Dict[str, Any]], outdir: str = '.selfhost_outputs') -> Dict[str, Any]:
    units = build_units_from_spec(spec)
    # annotate items with covers_units
    items = bind_units_to_items(units, items)

    covered = []
    partially = []
    uncovered = []
    for u in units:
        uid = u.get('id')
        # Skip matching structural dump requirements (fallback extractor cases)
        if u.get('structural_dump'):
            matched_items = []
        else:
            matched_items = [it for it in items if uid in (it.get('covers_units') or [])]
        # consider covered if at least one matched and not INVALID
        valid_matched = [it for it in matched_items if it.get('quality_status') != 'INVALID']
        if valid_matched:
            covered.append(uid)
        elif matched_items:
            partially.append(uid)
        else:
            uncovered.append({'id': uid, 'ptr': u.get('ptr'), 'text': u.get('text'), 'kind': u.get('kind'), 'structural_dump': bool(u.get('structural_dump'))})

    total = len(units)
    covered_count = len(covered)
    pct = (covered_count / total) if total else 1.0

    report = {
        'total_units': total,
        'covered_count': covered_count,
        'covered_pct': pct,
        'uncovered_units': sorted(uncovered, key=lambda x: (x.get('kind') or '', x.get('ptr') or '', x.get('id') or '')),
        'structural_unit_ids': sorted([u.get('id') for u in units if u.get('structural_dump')])
    }

    # persist
    try:
        os.makedirs(outdir, exist_ok=True)
        p = os.path.join(outdir, 'spec_coverage.json')
        with open(p + '.tmp', 'w', encoding='utf8') as f:
            json.dump(report, f, indent=2, sort_keys=True)
        os.replace(p + '.tmp', p)
    except Exception:
        pass

    # also persist annotated checklist for visibility
    try:
        clp = os.path.join(outdir, 'checklist.json')
        if os.path.exists(clp):
            cl = json.load(open(clp))
            items_out = items
            cl['items'] = items_out
            with open(clp + '.tmp', 'w', encoding='utf8') as f:
                json.dump(cl, f, indent=2, sort_keys=True)
            os.replace(clp + '.tmp', clp)
    except Exception:
        pass

    return report
