from dataclasses import dataclass
from typing import Union, Sequence


@dataclass(frozen=True)
class VerificationProperty:
    """Immutable dataclass describing a verification property.

    Fields:
    - id: stable identifier for the property (e.g., "VP-01")
    - description: short human-readable description
    - scope: single scope name or sequence of scopes where the property applies
    - severity: one of ('low', 'medium', 'high', 'critical')
    - deterministic: whether the property is expected to be deterministic
    """

    id: str
    description: str
    scope: Union[str, Sequence[str]]
    severity: str
    deterministic: bool = True
