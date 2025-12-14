from typing import List, Dict
from .properties import VerificationProperty


def check_spec_checklist_trace(items: List[Dict]) -> List[Dict]:
    """Return list of checklist items missing valid spec_pointer.

    Each returned dict contains item id and reason.
    """
    violations = []
    for item in items:
        spec_ptr = item.get("spec_pointer")
        if not spec_ptr or not isinstance(spec_ptr, str) or not spec_ptr.startswith("/"):
            violations.append({
                "id": item.get("id"),
                "ptr": item.get("ptr"),
                "reason": "invalid_or_missing_spec_pointer"
            })
    return violations


# Property descriptor for registry (informational only)
SPEC_CHECKLIST_TRACE_PROPERTY = VerificationProperty(
    id="VP-05-SPEC-CHECKLIST-TRACE_COMPLETE",
    description="All checklist items must have explicit, valid spec pointers (spec_pointer).",
    scope="checklist",
    severity="error",
    deterministic=True,
)
