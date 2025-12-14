from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class VerificationReport:
    passed: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
