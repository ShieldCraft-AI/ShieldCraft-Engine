"""Deterministic requirement extractor for spec prose.

Provides `extract_requirements(spec_text)` which returns a list of requirement dicts:
  - id: sha256(ptr + normalized_text)[:12]
  - type: MUST/SHOULD/MAY
  - scope: ptr string (e.g., /section/5.3 or /)
  - text: original text
  - norm: normalized text used for hashing
  - hash: sha256(norm)[:12]
"""
from __future__ import annotations

import hashlib
import re
from typing import List, Dict


MUST_KEYWORDS = ["must", "shall", "requires", "mandatory", "enforced", "every run must"]
SHOULD_KEYWORDS = ["should"]
MAY_KEYWORDS = ["may"]


def _normalize_text(s: str) -> str:
    s2 = s.lower()
    s2 = re.sub(r"[\t\n\r]+", " ", s2)
    s2 = re.sub(r"[\s]+", " ", s2).strip()
    s2 = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", s2)
    return s2


def _shorten(h: str) -> str:
    return h[:12]


def extract_requirements(spec_text: str) -> List[Dict]:
    """Extract normative requirements deterministically from raw spec text.

    Returns a list of lightweight dicts (compatible with Requirement domain model).
    """
    lines = spec_text.splitlines()
    reqs = []
    seen = set()
    current_section = None
    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        # ignore example blocks and headings ending with ':'
        if line.endswith(":"):
            continue
        if line.startswith("Example") or line.startswith("example"):
            continue
        # detect numbered section headings like '5.3 Enforced Restraint'
        m = re.match(r"^(\d+(?:\.\d+)*)\b\s*(.*)$", line)
        if m:
            current_section = m.group(1)
            continue

        low = line.lower()
        # check for normative keywords (MUST > SHOULD > MAY)
        kind = None
        if any(low.find(k) != -1 for k in MUST_KEYWORDS):
            kind = 'MUST'
        elif any(low.find(k) != -1 for k in SHOULD_KEYWORDS):
            kind = 'SHOULD'
        elif any(low.find(k) != -1 for k in MAY_KEYWORDS):
            kind = 'MAY'
        else:
            continue

        # skip short title-like lines
        tok_count = len(re.findall(r"[a-zA-Z0-9]+", line))
        if tok_count <= 3:
            continue

        norm = _normalize_text(line)
        if not norm:
            continue

        ptr = f"/section/{current_section}" if current_section else "/"
        h = _shorten(hashlib.sha256(norm.encode()).hexdigest())
        rid = _shorten(hashlib.sha256((ptr + norm).encode()).hexdigest())
        if (ptr, h) in seen:
            continue
        seen.add((ptr, h))
        reqs.append({
            'id': rid,
            'type': kind,
            'scope': ptr,
            'text': line,
            'norm': norm,
            'ptr': ptr,
            'hash': h,
            'line': i,
        })

    # sort deterministically by ptr then hash (stable across runs)
    reqs = sorted(reqs, key=lambda r: (r.get('ptr') or '/', r.get('hash') or r.get('id')))
    return reqs
