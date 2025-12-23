from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any
import json
import os
import re


class CoverageStatus(Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


@dataclass
class RequirementCoverage:
    requirement_id: str
    checklist_item_ids: List[str]
    coverage_status: CoverageStatus


def _tokenize(s: str):
    return re.findall(r"[a-z0-9]+", (s or '').lower())


def _overlap_ratio(req_text: str, quote: str) -> float:
    req_toks = _tokenize(req_text)
    if not req_toks:
        return 0.0
    quote_toks = set(_tokenize(quote))
    overlap = len(set(req_toks) & quote_toks)
    return overlap / len(req_toks)


def compute_coverage(requirements: List[Dict[str, Any]],
                     checklist_items: List[Dict[str, Any]]) -> List[RequirementCoverage]:
    res: List[RequirementCoverage] = []
    # Build quick indices

    for r in sorted(requirements, key=lambda x: x.get('id')):
        rid = r.get('id')
        req_text = r.get('text') or ''
        req_ptr = r.get('ptr') or r.get('source_ptr') or r.get('ptr')
        matched_ids = []
        strong = False

        for it in checklist_items:
            it_id = it.get('id')
            ev = it.get('evidence') or {}
            src = ev.get('source') or {}
            iptr = src.get('ptr') or ''
            ihash = ev.get('source_excerpt_hash') or ''
            quote = ev.get('quote') or ''
            # direct pointer relation
            if iptr and (iptr == req_ptr or iptr.startswith((req_ptr or '').rstrip('/') + '/')):
                matched_ids.append(it_id)
                # consider as strong if priority is P0/P1 and confidence not low
                if (it.get('priority') in ('P0', 'P1')) and ((it.get('confidence') or '').lower() != 'low'):
                    strong = True
                continue
            # excerpt hash match
            if ihash and ihash == r.get('hash'):
                matched_ids.append(it_id)
                if (it.get('priority') in ('P0', 'P1')) and ((it.get('confidence') or '').lower() != 'low'):
                    strong = True
                continue
            # overlap check
            if quote:
                ratio = _overlap_ratio(req_text, quote)
                if ratio >= 0.6:
                    matched_ids.append(it_id)
                    if (it.get('priority') in ('P0', 'P1')) and ((it.get('confidence') or '').lower() != 'low'):
                        strong = True

        if not matched_ids:
            status = CoverageStatus.MISSING
        elif strong:
            status = CoverageStatus.FULL
        else:
            status = CoverageStatus.PARTIAL

        res.append(
            RequirementCoverage(
                requirement_id=rid,
                checklist_item_ids=sorted(
                    set(matched_ids)),
                coverage_status=status))

    return res


def write_coverage_report(covers: List[RequirementCoverage], outdir: str = '.selfhost_outputs') -> str:
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, 'coverage.json')
    data = [{'requirement_id': c.requirement_id,
             'checklist_item_ids': c.checklist_item_ids,
             'coverage_status': c.coverage_status.value} for c in covers]
    with open(p, 'w', encoding='utf8') as f:
        json.dump({'coverage': data}, f, indent=2, sort_keys=True)
    return p
