from typing import Dict, List


def validate_test_contract(items: List[Dict]) -> List[Dict]:
    """Validate that each checklist item has explicit test_refs list.

    Returns list of violations: {id, ptr, reason}
    """
    violations = []
    for it in items:
        refs = it.get("test_refs")
        if not refs or not isinstance(refs, (list, tuple)) or len(refs) == 0:
            violations.append({"id": it.get("id"), "ptr": it.get("ptr"), "reason": "missing_test_refs"})
    return violations
