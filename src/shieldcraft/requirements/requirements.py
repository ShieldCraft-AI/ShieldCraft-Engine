from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List


@dataclass(frozen=True)
class Requirement:
    id: str
    statement: str
    source_ptr: str
    category: str  # MUST/SHOULD/MAY
    mandatory: bool
    evidence_required: bool


def from_dict(d: dict) -> Requirement:
    return Requirement(
        id=d.get('id'),
        statement=d.get('text') or d.get('statement') or '',
        source_ptr=d.get('ptr') or d.get('scope') or d.get('source_ptr') or '/',
        category=d.get('type') or d.get('level') or 'MAY',
        mandatory=(d.get('type') == 'MUST' or d.get('level') == 'MUST'),
        evidence_required=(d.get('type') == 'MUST' or d.get('level') == 'MUST')
    )


def to_dict(r: Requirement) -> dict:
    return asdict(r)


def to_json_serializable(reqs: List[Requirement]) -> List[dict]:
    return [to_dict(r) for r in reqs]
