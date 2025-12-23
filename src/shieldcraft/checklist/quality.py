from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple
import json
import os
import re
import hashlib


@dataclass
class ItemQuality:
    item_id: str
    content_hash: str
    quality_status: str  # VALID or INVALID
    quality_reasons: List[str]
    low_signal: bool = False
    low_signal_reasons: List[str] = None


def _normalize_text(s: str) -> str:
    if s is None:
        return ''
    s2 = s.lower()
    s2 = re.sub(r"[\t\n\r]+", " ", s2)
    s2 = re.sub(r"[\s]+", " ", s2).strip()
    s2 = re.sub(r'["\'`\-–—]+', " ", s2)
    s2 = re.sub(r"[^a-z0-9 ]+", "", s2)
    return s2


def _content_hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


COMMON_IMPERATIVE_VERBS = {
    'add',
    'apply',
    'attach',
    'audit',
    'build',
    'check',
    'create',
    'deploy',
    'document',
    'enforce',
    'ensure',
    'fix',
    'implement',
    'install',
    'integrate',
    'merge',
    'produce',
    'refuse',
    'register',
    'remove',
    'replace',
    'run',
    'update',
    'validate',
    'verify'}


def evaluate_quality(items: List[Dict[str, Any]]) -> Tuple[List[ItemQuality], Dict[str, Any]]:
    """Evaluate checklist items for quality.

    Returns per-item quality and an aggregate summary.
    """
    seen_hashes = {}
    qualities: List[ItemQuality] = []

    for it in items:
        iid = it.get('id')
        text = (it.get('action') or it.get('text') or it.get('claim') or it.get('value') or '')
        norm = _normalize_text(text)
        ch = _content_hash(norm)
        reasons: List[str] = []

        # Must be actionable: have at least an imperative verb and >1 token
        toks = norm.split()
        if not toks or len(toks) < 2:
            reasons.append('non_actionable')
        else:
            first = toks[0]
            if first not in COMMON_IMPERATIVE_VERBS and not first.endswith('e'):
                # lenient: accept ensure/create/implement or words ending with 'e' as likely verbs
                reasons.append('non_actionable')

        # Falsifiable: must be markable done/not-done — simple heuristic: presence of verb + object
        if len(toks) < 2:
            reasons.append('non_falsifiable')

        # Must reference requirement via requirement_refs or evidence (best-effort)
        has_req = False
        if it.get('requirement_refs'):
            has_req = True
        else:
            ev = it.get('evidence') or {}
            if ev.get('source_excerpt_hash') or (ev.get('source') or {}).get('ptr'):
                has_req = True
        if not has_req:
            reasons.append('no_requirement_coverage')

        # Duplicate detection by (normalized content hash + ptr) to avoid false positives
        ptr = it.get('ptr') or ''
        key = (ch, ptr)
        if key in seen_hashes:
            reasons.append('duplicate')
        else:
            seen_hashes[key] = iid

        status = 'VALID' if not reasons else 'INVALID'
        # Low-signal detection (conservative): mark low-signal only when
        # (no artifact AND no execution effect) OR
        # (prose_restatement AND low_confidence) OR
        # (no_requirement_coverage AND low_confidence)
        low_reasons: List[str] = []
        no_artifact = False
        if not it.get('produces_artifacts') and not any(
            v in (
                it.get('covers_dimensions') or []) for v in (
                'artifacts',
                'refusal')):
            no_artifact = True
        no_execution = False
        if not (it.get('requires_item_ids') or it.get('depends_on') or it.get('produces_artifacts')
                or it.get('requires_artifacts') or it.get('order_rank') or it.get('blocking')):
            no_execution = True
        prose_restatement = bool(it.get('inferred_from_prose'))
        low_conf = (it.get('confidence') or '').lower() == 'low'
        if no_artifact and no_execution:
            low_reasons.append('no_artifact_and_no_execution')
        if prose_restatement and low_conf:
            low_reasons.append('prose_restatement_low_conf')
        # consider missing requirement coverage combined with low confidence as low-signal
        if 'no_requirement_coverage' in reasons and low_conf:
            low_reasons.append('no_requirement_coverage_low_conf')

        is_low = len(low_reasons) > 0

        qualities.append(
            ItemQuality(
                item_id=iid or '',
                content_hash=ch,
                quality_status=status,
                quality_reasons=sorted(
                    set(reasons)),
                low_signal=is_low,
                low_signal_reasons=sorted(
                    set(low_reasons))))

    # Compute aggregates
    total = len(qualities)
    invalid = sum(1 for q in qualities if q.quality_status == 'INVALID')
    duplicate = sum(1 for q in qualities if 'duplicate' in q.quality_reasons)
    low_signal_count = sum(1 for q in qualities if q.low_signal)
    offending_ids = sorted([q.item_id for q in qualities if q.low_signal])

    summary = {
        'total_items': total,
        'invalid_items': invalid,
        'duplicate_items': duplicate,
        'low_signal_count': low_signal_count,
        'low_signal_item_ids': offending_ids,
    }

    return qualities, summary


def write_quality_report(qualities: List[ItemQuality], summary: Dict[str, Any],
                         outdir: str = '.selfhost_outputs') -> str:
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, 'checklist_quality.json')
    data = {'items': [asdict(q) for q in qualities], 'summary': summary}
    with open(p, 'w', encoding='utf8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
    return p
