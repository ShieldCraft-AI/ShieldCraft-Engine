"""Explain differences between two runs at the smallest possible unit."""
from typing import Any, Dict, List
from shieldcraft.services.governance.determinism import DeterminismEngine


def explain_diff(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    de = DeterminismEngine()
    ca = de.canonicalize(a)
    cb = de.canonicalize(b)
    if ca == cb:
        return {"match": True}

    # Minimal explanation: top-level keys that differ
    diffs: List[str] = []
    for k in sorted(set(list(a.keys()) + list(b.keys()))):
        if a.get(k) != b.get(k):
            diffs.append(k)

    # For items, produce per-item id differences
    item_diffs = []
    ai = {it.get("id"): it for it in a.get("items", [])}
    bi = {it.get("id"): it for it in b.get("items", [])}
    for id_ in sorted(set(list(ai.keys()) + list(bi.keys()))):
        if ai.get(id_) != bi.get(id_):
            item_diffs.append({"id": id_, "a": ai.get(id_), "b": bi.get(id_)})

    return {"match": False, "diff_keys": diffs, "item_diffs_count": len(
        item_diffs), "item_diffs_sample": item_diffs[:5]}
