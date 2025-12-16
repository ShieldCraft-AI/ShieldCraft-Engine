from __future__ import annotations

from enum import Enum
from typing import Dict


class ConversionState(Enum):
    ACCEPTED = "ACCEPTED"
    CONVERTIBLE = "CONVERTIBLE"
    STRUCTURED = "STRUCTURED"
    VALID = "VALID"
    READY = "READY"
    INCOMPLETE = "INCOMPLETE"

# NOTE: The conversion state ladder is frozen for SE v1. Any changes to this
# enumeration (adding, removing, or renaming states) require a schema bump
# and an explicit decision recorded in `docs/decision_log.md` and a release
# note in `docs/SE_V1_CLOSED.md`.


_ORDER = {
    ConversionState.ACCEPTED: 0,
    ConversionState.CONVERTIBLE: 1,
    ConversionState.STRUCTURED: 2,
    ConversionState.VALID: 3,
    ConversionState.READY: 4,
    ConversionState.INCOMPLETE: 5,
}


def is_at_least(current: ConversionState, target: ConversionState) -> bool:
    return _ORDER.get(current, -1) >= _ORDER.get(target, -1)


def to_dict(state: ConversionState, reason: str | None = None) -> Dict:
    return {"conversion_state": state.value, "state_reason": reason}
