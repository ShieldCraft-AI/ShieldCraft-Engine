from typing import List, Dict
from .test_coverage import check_checklist_test_coverage


def check_checklist_to_test(items: List[Dict]) -> List[Dict]:
    """Verify every checklist item references >=1 test. Reuses Phase 4 check."""
    return check_checklist_test_coverage(items)
