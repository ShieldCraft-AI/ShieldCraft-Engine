from __future__ import annotations
from typing import List
from .interpreter import interpret_raw_spec
from shieldcraft.checklist.item_v1 import ChecklistItemV1


class RawSpecInterpreter:
    """Interpreter that derives checklist items from raw spec text.

    It is intentionally lightweight and deterministic. It wraps the
    lower-level `interpret_raw_spec` implementation and returns a list
    of dicts (serializable) for downstream consumption.
    """

    def interpret(self, text: str) -> List[dict]:
        items: List[ChecklistItemV1] = interpret_raw_spec(text or "") or []
        return [it.to_dict() for it in items]
