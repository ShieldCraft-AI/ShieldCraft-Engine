from typing import Dict, List
from .properties import VerificationProperty


class VerificationRegistry:
    """In-memory registry for verification properties."""

    def __init__(self) -> None:
        self._by_id: Dict[str, VerificationProperty] = {}

    def register(self, prop: VerificationProperty) -> None:
        if prop.id in self._by_id:
            raise ValueError(f"Duplicate property id: {prop.id}")
        self._by_id[prop.id] = prop

    def get_all(self) -> List[VerificationProperty]:
        return list(self._by_id.values())

    def get_by_scope(self, scope: str) -> List[VerificationProperty]:
        out: List[VerificationProperty] = []
        for p in self._by_id.values():
            s = p.scope
            if isinstance(s, str) and s == scope:
                out.append(p)
            elif isinstance(s, (list, tuple)) and scope in s:
                out.append(p)
        return out


_GLOBAL_REGISTRY = VerificationRegistry()


def global_registry() -> VerificationRegistry:
    return _GLOBAL_REGISTRY
