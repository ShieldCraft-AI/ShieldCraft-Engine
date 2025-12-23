from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class ChecklistItemV1:
    id: str
    claim: str
    obligation: Optional[str]
    risk_if_false: str
    confidence: str  # 'LOW'|'MEDIUM'|'HIGH'
    evidence_ref: Dict

    def to_dict(self):
        return {
            "id": str(self.id),
            "claim": self.claim,
            "obligation": self.obligation,
            "risk_if_false": self.risk_if_false,
            "confidence": self.confidence,
            "evidence_ref": self.evidence_ref,
        }
