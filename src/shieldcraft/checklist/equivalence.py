from __future__ import annotations

from typing import List, Dict, Any, Tuple
import hashlib
import json
import os

from shieldcraft.requirements.completion import evaluate_completeness


def _norm_text(s: str) -> str:
    if s is None:
        return ''
    return ' '.join(str(s).lower().split())


def _artifact_signature(item: Dict[str, Any]) -> str:
    parts = []
    # Prefer explicit obligation/value/claim
    for k in ('obligation', 'value', 'claim', 'action', 'text'):
        v = item.get(k)
        if v:
            parts.append(_norm_text(v))
            break
    # include explicit evidence pointers/hashes
    ev = item.get('evidence') or {}
    if ev.get('source_excerpt_hash'):
        parts.append(str(ev.get('source_excerpt_hash')))
    if (ev.get('source') or {}).get('ptr'):
        parts.append(str((ev.get('source') or {}).get('ptr')))
    # include intent_category if present
    if item.get('intent_category'):
        parts.append(_norm_text(item.get('intent_category')))
    # deterministic signature
    s = '\n'.join(parts)
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def group_equivalent_items(items: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    # Group by (requirement_refs, artifact_signature, risk_if_false, readiness_impact)
    groups = {}
    for it in items:
        reqs = tuple(sorted(it.get('requirement_refs') or []))
        sig = _artifact_signature(it)
        risk = it.get('risk_if_false')
        readiness = it.get('readiness_impact') or it.get('readiness')
        key = (reqs, sig, str(risk), str(readiness))
        groups.setdefault(key, []).append(it)
    # Only return groups with more than 1 item as potential equivalence classes
    res = []
    for k, g in groups.items():
        if len(g) > 1:
            # sort deterministically by id so downstream selection is stable
            g_sorted = sorted(g, key=lambda x: x.get('id') or '')
            res.append(g_sorted)
    return sorted(res, key=lambda g: [i.get('id') for i in g])


def choose_primary(group: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Choose primary by: priority (P0 highest), then most specific (max covers_dimensions), then confidence, then id
    def priority_val(it):
        p = it.get('priority') or it.get('priority_rank') or ''
        if isinstance(p, str) and p.upper().startswith('P') and len(p) >= 2 and p[1].isdigit():
            try:
                return int(p[1])
            except Exception:
                pass
        # default mid value
        return 5

    def confidence_val(it):
        c = (it.get('confidence') or '').upper()
        order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, '': 0}
        return order.get(c, 0)

    best = None
    for it in group:
        if best is None:
            best = it
            continue
        # compare priority (lower is better)
        if priority_val(it) < priority_val(best):
            best = it
            continue
        # prefer more specific (more dimensions)
        if len(it.get('covers_dimensions') or []) > len(best.get('covers_dimensions') or []):
            best = it
            continue
        # confidence
        if confidence_val(it) > confidence_val(best):
            best = it
            continue
        # deterministic tie-breaker: id
        if (it.get('id') or '') < (best.get('id') or ''):
            best = it
    return best


def detect_and_collapse(items: List[Dict[str, Any]], requirements: List[Dict[str, Any]], outdir: str = '.selfhost_outputs') -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    groups = group_equivalent_items(items)
    collapsed_map = {}
    removed = 0
    # initial completeness for proof
    orig_results, orig_summary = evaluate_completeness(requirements, items)
    orig_complete = orig_summary.get('complete_pct', 0.0)

    for g in groups:
        primary = choose_primary(g)
        others = [it for it in g if it.get('id') != primary.get('id')]
        if not others:
            continue
        primary_id = primary.get('id')
        collapsed_map[primary_id] = [it.get('id') for it in others]
        removed += len(others)

    # Build pruned items list by removing any item id present in collapsed_map values
    removed_ids = {rid for vals in collapsed_map.values() for rid in vals}
    pruned = [it for it in items if it.get('id') not in removed_ids]

    # Attach traceability: collapsed_from list on primaries
    for pid, vals in collapsed_map.items():
        for it in pruned:
            if it.get('id') == pid:
                it['collapsed_from'] = sorted(vals)

    # Proof of minimality: removing any PRIMARY must reduce completeness
    proof = []
    # Build mapping of primary ids
    primary_ids = list(collapsed_map.keys())
    for pid in primary_ids:
        items_minus = [it for it in pruned if it.get('id') != pid]
        _, summary = evaluate_completeness(requirements, items_minus)
        delta = orig_complete - summary.get('complete_pct', 0.0)
        proof.append({'primary': pid, 'necessary': delta > 0.0, 'delta_complete_pct': delta})

    report = {
        'removed_count': removed,
        'equivalence_groups': [{'primary': k, 'collapsed_from': v} for k, v in sorted(collapsed_map.items())],
        'proof_of_minimality': proof,
        'original_complete_pct': orig_complete,
        'result_complete_pct': evaluate_completeness(requirements, pruned)[1].get('complete_pct')
    }

    # Persist report deterministically
    try:
        os.makedirs(outdir, exist_ok=True)
        p = os.path.join(outdir, 'checklist_minimality.json')
        with open(p + '.tmp', 'w', encoding='utf8') as f:
            json.dump(report, f, indent=2, sort_keys=True)
        os.replace(p + '.tmp', p)
    except Exception:
        pass

    return pruned, report
