"""Deterministic spec mutation utilities for adversarial testing."""
from copy import deepcopy
from typing import Dict, List, Tuple
from .failure_classes import SPEC_AMBIGUOUS, SPEC_CONTRADICTORY, SPEC_INCOMPLETE, SPEC_STABLE


def generate_mutations(spec: Dict) -> List[Tuple[Dict, str, str]]:
    """Generate a deterministic set of spec mutations.

    Returns list of tuples: (mutated_spec, mutation_kind, description)
    """
    muts = []

    # 1) omission: remove each top-level section (if any)
    sections = spec.get("sections")
    if isinstance(sections, dict):
        for k in sorted(sections.keys()):
            s = deepcopy(spec)
            s2 = s.get("sections", {})
            if k in s2:
                del s2[k]
            muts.append((s, "omission", f"removed_section:{k}"))

    # 2) contradiction: duplicate a section id with conflicting payload
    if isinstance(sections, dict) and sections:
        for k in sorted(sections.keys())[:1]:  # only create one conflicting variant for determinism
            s = deepcopy(spec)
            s2 = s.get("sections", {})
            # create conflicting copy
            s2[f"conflict_{k}"] = {"id": sections[k].get("id", f"{k}"), "description": "conflict"}
            muts.append((s, "contradiction", f"duplicate_conflicting_section:{k}"))

    # 3) reordering: if sections is a list, reverse it
    if isinstance(sections, list) and len(sections) > 1:
        s = deepcopy(spec)
        s["sections"] = list(reversed(s["sections"]))
        muts.append((s, "reorder", "reversed_sections"))

    # 4) omission of metadata
    if "metadata" in spec:
        s = deepcopy(spec)
        s.pop("metadata", None)
        muts.append((s, "omission", "removed_metadata"))

    return muts


def classify_mutation(original: Dict, mutated: Dict, mutation_kind: str) -> str:
    """Classify the mutation impact using simple heuristics.

    - Removing metadata -> SPEC_INCOMPLETE
    - Introducing a conflicting section id -> SPEC_CONTRADICTORY
    - Reordering sections -> SPEC_STABLE (benign)
    - Removing a section that existed -> SPEC_AMBIGUOUS (could change requirements)
    """
    if mutation_kind == "omission":
        # If metadata removed -> incomplete
        if "metadata" not in mutated:
            return SPEC_INCOMPLETE
        # If a section removed compared to original -> ambiguous
        orig_secs = set(original.get("sections", {}).keys() if isinstance(original.get("sections"), dict) else [])
        mut_secs = set(mutated.get("sections", {}).keys() if isinstance(mutated.get("sections"), dict) else [])
        if orig_secs - mut_secs:
            return SPEC_AMBIGUOUS
        return SPEC_STABLE
    if mutation_kind == "contradiction":
        return SPEC_CONTRADICTORY
    if mutation_kind == "reorder":
        return SPEC_STABLE
    return SPEC_STABLE
