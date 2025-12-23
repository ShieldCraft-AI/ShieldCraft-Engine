"""Build deterministic artifact contract summaries from explicit intents.

Rules:
- Only include artifacts explicitly referenced in the spec's `artifact_contract`,
  checklist items (`artifact_type`), or execution_preview (`would_generate`).
- Classification by `conversion_state`:
  - READY: all referenced artifacts -> `guaranteed`
  - STRUCTURED or VALID: referenced artifacts -> `conditional`
  - below STRUCTURED: referenced artifacts -> `unavailable`
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional, Set


def _collect_referenced_artifacts(artifact_contract: Optional[Dict[str,
                                                                   Any]],
                                  checklist_items: Optional[List[Dict[str,
                                                                      Any]]],
                                  execution_preview: Optional[Dict[str,
                                                                   Any]]) -> List[str]:
    refs: Set[str] = set()
    if artifact_contract and isinstance(artifact_contract, dict):
        ar = artifact_contract.get("artifacts", []) or []
        for a in ar:
            if isinstance(a, dict) and a.get("id"):
                refs.add(a.get("id"))
            elif isinstance(a, str):
                refs.add(a)
    if checklist_items:
        for it in checklist_items:
            if isinstance(it, dict) and it.get("artifact_type"):
                refs.add(it.get("artifact_type"))
    if execution_preview and isinstance(execution_preview, dict):
        for a in execution_preview.get("would_generate", []):
            refs.add(a)
    return sorted(refs)


def build_artifact_contract_summary(conversion_state: Optional[str],
                                    artifact_contract: Optional[Dict[str,
                                                                     Any]],
                                    checklist_items: Optional[List[Dict[str,
                                                                        Any]]],
                                    execution_preview: Optional[Dict[str,
                                                                     Any]]) -> Dict[str,
                                                                                    List[str]]:
    cur = (conversion_state or "").upper()
    refs = _collect_referenced_artifacts(artifact_contract, checklist_items, execution_preview)

    guaranteed: List[str] = []
    conditional: List[str] = []
    unavailable: List[str] = []

    if not refs:
        return {"guaranteed": [], "conditional": [], "unavailable": []}

    if cur == "READY":
        guaranteed = refs
    elif cur in ("VALID", "STRUCTURED"):
        # If execution_preview lists an artifact, it must be conditional; ensure included
        conditional = refs
    else:
        unavailable = refs

    return {"guaranteed": sorted(guaranteed), "conditional": sorted(conditional), "unavailable": sorted(unavailable)}
