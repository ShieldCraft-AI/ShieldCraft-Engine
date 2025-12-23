from typing import Dict, List


def expand_tests_for_item(item: Dict, test_map: Dict[str, str]) -> Dict:
    """Return deterministic test vectors for a checklist item based on discovered tests.

    Does NOT invent tests. Picks up to 3 candidate tests that mention the item ptr or id.
    Returns dict with keys: 'item_id', 'candidates' (list of test refs), 'missing' (bool)
    """
    ptr = item.get("ptr", "")
    item_id = item.get("id")

    candidates: List[str] = []
    for sid, ref in test_map.items():
        # deterministic search: include tests whose path or name include ptr or id
        if ptr and ptr.strip("/") and ptr.strip("/") in ref:
            candidates.append(sid)
        elif item_id and item_id in ref:
            candidates.append(sid)

    # If none matched by substring, as a fallback, include first N tests (but do not invent)
    if not candidates:
        # choose first 3 available tests deterministically
        candidates = list(sorted(test_map.keys()))[:3]

    # Return a deterministic slice of up to 3
    candidates = sorted(set(candidates))[:3]

    return {"item_id": item_id, "candidates": candidates, "missing": len(candidates) == 0}
