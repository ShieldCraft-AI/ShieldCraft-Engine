from typing import List, Dict
from .properties import VerificationProperty


def check_checklist_test_coverage(items: List[Dict]) -> List[Dict]:
    """Return list of checklist items missing test coverage.

    Each returned dict contains item id and reason.
    """
    violations = []
    for item in items:
        refs = item.get("test_refs")
        if not refs or not isinstance(refs, (list, tuple)) or len(refs) == 0:
            violations.append({
                "id": item.get("id"),
                "ptr": item.get("ptr"),
                "reason": "missing_test_refs"
            })
    return violations


CHECKLIST_TEST_COVERAGE_PROPERTY = VerificationProperty(
    id="VP-06-CHECKLIST-TEST-COVERAGE_COMPLETE",
    description="All checklist items must explicitly reference at least one test identifier.",
    scope="checklist",
    severity="error",
    deterministic=True,
)
