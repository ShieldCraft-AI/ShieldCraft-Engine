"""Test Attachment Contract (TAC) v1 enforcement utilities."""
from typing import List, Any


class ProductInvariantFailure(RuntimeError):
    def __init__(self, code: str, offending: List[str]):
        super().__init__(f"{code}:{offending}")
        self.code = code
        self.offending = offending


def verify_tests_attached(checklist: Any) -> None:
    """Verify that each checklist item declares a non-empty `test_refs` array.

    Raises `ProductInvariantFailure` with code `tests_attached` and offending
    item ids if any violations are found.
    """
    items = checklist.get("items") if isinstance(checklist, dict) else checklist
    if items is None:
        raise ProductInvariantFailure("tests_attached", ["no_items_found"])

    offending = []
    for it in items:
        tid = it.get("id")
        tr = it.get("test_refs", None)
        if tr is None:
            offending.append(tid)
            continue
        if not isinstance(tr, list) or len(tr) < 1:
            offending.append(tid)
            continue
        # ensure all entries are strings
        if any(not isinstance(x, str) or not x for x in tr):
            offending.append(tid)

    if offending:
        raise ProductInvariantFailure("tests_attached", offending)
