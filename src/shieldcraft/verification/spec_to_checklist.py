from typing import List, Dict
from shieldcraft.services.ast.lineage import get_spec_id_map


def check_spec_to_checklist(ast, checklist_items: List[Dict]) -> List[Dict]:
    """Verify every spec clause (spec_id) is referenced by >=1 checklist item.

    Returns list of violations with spec_id and pointer.
    """
    violations = []

    spec_map = get_spec_id_map(ast)  # ptr -> spec_id

    # Build reverse mapping: spec_id -> ptr
    spec_id_to_ptr = {v: k for k, v in spec_map.items()}

    # Helper to check if a spec ptr is covered by any checklist item
    def ptr_covered(spec_ptr):
        for it in checklist_items:
            iptr = it.get("ptr", "")
            if iptr == spec_ptr or iptr.startswith(spec_ptr + "/"):
                return True
        return False

    for sid, ptr in spec_id_to_ptr.items():
        if not ptr_covered(ptr):
            violations.append({"spec_id": sid, "ptr": ptr, "reason": "orphan_spec_clause"})

    return violations
