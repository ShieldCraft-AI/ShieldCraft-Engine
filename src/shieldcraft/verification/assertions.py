from typing import Iterable
from .properties import VerificationProperty


_ALLOWED_SEVERITIES = {"low", "medium", "high", "critical", "error"}


def assert_verification_properties(properties: Iterable[VerificationProperty]) -> None:
    """Validate basic well-formedness of verification properties.

    Raises RuntimeError on the first detected violation.
    """
    for p in properties:
        if not p.id or not isinstance(p.id, str):
            raise RuntimeError("Invalid property id")
        if not p.description:
            raise RuntimeError("Property missing description")
        if not p.severity or p.severity not in _ALLOWED_SEVERITIES:
            raise RuntimeError("Invalid property severity")
        # scope may be string or sequence; basic check only
        if not p.scope:
            raise RuntimeError("Property missing scope")
