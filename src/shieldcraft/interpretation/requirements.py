"""Requirement extraction for interpretation stage.

Provides `extract_requirements(raw_text)` which returns deterministic requirement objects:
  - id: sha256(ptr + norm_text)[:12]
  - text: original sentence
  - ptr: section pointer or '/'
  - modality: MUST/SHOULD/MAY
  - strength: structural|behavioral|governance
  - excerpt_hash: sha256(norm_text)[:12]
"""
from __future__ import annotations

import hashlib
import re
from typing import List, Dict


MODALITY_KEYWORDS = {
    'MUST': ["must", "required", "enforced", "non-negotiable", "every run must"],
    'SHOULD': ["should", "recommended", "expected"],
    'MAY': ["may", "optional", "allowed"],
}


def _normalize(s: str) -> str:
    s2 = s.lower()
    s2 = re.sub(r"[\s\t\n\r]+", " ", s2).strip()
    s2 = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", s2)
    return s2


def _short(h: str) -> str:
    return h[:12]


def _classify_strength(norm: str) -> str:
    # structural if determinism, artifact, refusal, safety
    structural_kw = [
        'determin',
        'artifact',
        'signature',
        'refuse',
        'refusal',
        'safety',
        'no-touch',
        'no-touch',
        'no-touch-zone']
    behavioral_kw = ['runtime', 'behavior', 'performance', 'response', 'behavioral']
    governance_kw = ['policy', 'govern', 'enforce', 'blocking', 'contract', 'tests', 'contract']
    for k in structural_kw:
        if k in norm:
            return 'structural'
    for k in governance_kw:
        if k in norm:
            return 'governance'
    for k in behavioral_kw:
        if k in norm:
            return 'behavioral'
    # default structural for normative language
    return 'structural'


def extract_requirements(raw_text: str) -> List[Dict]:
    reqs = []
    seen = set()
    current_section = None
    for i, line in enumerate(raw_text.splitlines(), start=1):
        s = line.strip()
        if not s:
            continue
        # skip headings and examples
        if s.endswith(':') or s.lower().startswith('example'):
            continue
        # detect numbered section headings
        m = re.match(r"^(\d+(?:\.\d+)*)\b", s)
        if m:
            current_section = m.group(1)
            # skip the heading line itself
            continue

        low = s.lower()
        # Determine modality
        modality = None
        for mod, kws in MODALITY_KEYWORDS.items():
            if any(kw in low for kw in kws):
                modality = mod
                break
        if not modality:
            # Ignore narrative-only prose (no action verb)
            # Heuristic: require a verb-like token
            if not re.search(
                r"\b(is|are|be|have|provide|include|emit|produce|refuse|enforce|require|must|should|may)\b",
                    low):
                continue
            else:
                modality = 'MAY'

        norm = _normalize(s)
        if not norm:
            continue

        ptr = f"/section/{current_section}" if current_section else '/'
        excerpt_hash = _short(hashlib.sha256(norm.encode()).hexdigest())
        rid = _short(hashlib.sha256((ptr + norm).encode()).hexdigest())
        if (ptr, excerpt_hash) in seen:
            continue
        seen.add((ptr, excerpt_hash))

        strength = _classify_strength(norm)

        reqs.append({
            'id': rid,
            'text': s,
            'ptr': ptr,
            'modality': modality,
            'strength': strength,
            'excerpt_hash': excerpt_hash,
            'line': i,
        })

    # deterministic ordering
    return sorted(reqs, key=lambda r: r['id'])
