"""Checklist annotation utilities.

Annotates checklist items with `applicable_states` and `relevance_reason` and
computes a summary derived from these annotations.
"""
from __future__ import annotations

from typing import List, Dict


# Static mapping by classification keywords to relevance and applicable states.
# Deterministic and code-defined; can be extended as needed.
CLASSIFICATION_MAP = {
    # Items that block readiness (require VALID)
    "resolve-invariant": {"applicable_states": ["VALID", "READY"], "relevance_reason": "blocks readiness"},
    "resolve-cycle": {"applicable_states": ["VALID", "READY"], "relevance_reason": "blocks readiness"},
    # Dependency fixes are actionable early
    "fix-dependency": {"applicable_states": ["CONVERTIBLE", "STRUCTURED", "VALID", "READY"], "relevance_reason": "dependency"},
    # Bootstrap helpers are early-stage
    "bootstrap": {"applicable_states": ["CONVERTIBLE", "STRUCTURED", "VALID", "READY"], "relevance_reason": "bootstrap"},
}


def annotate_items(items: List[Dict]) -> List[Dict]:
    """Annotate items in-place (and return items) deterministically.

    Adds `applicable_states` and `relevance_reason` keys when absent.
    Does not change ordering or ids.
    """
    for it in items:
        if "applicable_states" in it and "relevance_reason" in it:
            continue
        # Determine classification key
        cls = it.get("classification") or it.get("type") or ""
        entry = CLASSIFICATION_MAP.get(cls, None)
        if entry is None:
            # Fallback: default to all states
            it["applicable_states"] = ["CONVERTIBLE", "STRUCTURED", "VALID", "READY"]
            it["relevance_reason"] = "routine"
        else:
            it["applicable_states"] = entry["applicable_states"]
            it["relevance_reason"] = entry["relevance_reason"]
    return items


def checklist_summary(items: List[Dict], current_state: str) -> Dict:
    total = len(items)
    items_relevant_now = 0
    items_blocking = 0
    for it in items:
        apps = it.get("applicable_states", [])
        if current_state in apps:
            items_relevant_now += 1
        # Blocking if relevance_reason indicates blocking and not applicable now
        if it.get("relevance_reason") == "blocks readiness" and current_state not in apps:
            items_blocking += 1
    items_future = total - items_relevant_now
    return {
        "total_items": total,
        "items_relevant_now": items_relevant_now,
        "items_future": items_future,
        "items_blocking_progress": items_blocking,
    }


def annotate_items_with_blockers(items: List[Dict], validation_errors: List[str] | None = None, readiness_results: Dict | None = None) -> List[Dict]:
    """Annotate checklist items with `status` and `blocked_by` based on validation/readiness.

    - If `validation_errors` is non-empty: all items get `status` = "draft" and `blocked_by` = validation_errors.
    - Else if `readiness_results` indicates failing gates: items get `status` = "blocked" and `blocked_by` = [failing_gate_keys].
    - Otherwise: `status` = "ok" and `blocked_by` = [].
    """
    val_errors = validation_errors or []
    failing_gates = []
    if readiness_results and isinstance(readiness_results, dict):
        for k, v in sorted((readiness_results.get("results") or {}).items()):
            if isinstance(v, dict) and not v.get("ok"):
                failing_gates.append(k)
    for it in items:
        if val_errors:
            it["status"] = "draft"
            it["blocked_by"] = list(val_errors)
        elif failing_gates:
            it["status"] = "blocked"
            it["blocked_by"] = list(failing_gates)
        else:
            it["status"] = "ok"
            it["blocked_by"] = []
    return items


def enrich_with_confidence_and_evidence(items: List[Dict], spec: Dict | None = None) -> List[Dict]:
    """Add `confidence`, `evidence`, `inferred_from_prose`, and `intent_category` to each item.

    - Confidence: 'high' | 'medium' | 'low' (default low for prose-derived, high for DSL-derived)
    - Evidence: {'source': {'ptr': ptr, 'line': line}, 'source_excerpt_hash': ...}
    - inferred_from_prose: True when derived from prose-like strings or sections
    - intent_category: one of safety, refusal, determinism, governance, output_contract, or misc
    """
    import hashlib
    from ..checklist.extractor import SpecExtractor
    extractor = SpecExtractor()

    # Keyword-driven intent mapping
    intent_map = {
        "must": "safety",
        "must not": "refusal",
        "never": "refusal",
        "requires": "governance",
        "refuse": "refusal",
        "determin": "determinism",
        "artifact": "output_contract",
        "output": "output_contract",
        "policy": "governance",
        "governance": "governance",
        "safe": "safety",
    }

    for it in items:
        ptr = it.get("ptr")
        value = it.get("value")
        text = it.get("text", "")

        # Base evidence.source
        try:
            line = extractor._compute_line(ptr)
        except Exception:
            line = None
        it.setdefault("evidence", {})
        it["evidence"]["source"] = {"ptr": ptr, "line": line}

        # Default flags
        it["inferred_from_prose"] = False
        # Heuristic: prose if value is a string or the generated text contains obligation language
        is_prose = False
        lowv = ""
        if isinstance(value, str):
            lowv = value.lower()
        if isinstance(text, str):
            lowtxt = text.lower()
        else:
            lowtxt = ""
        if "/sections" in (ptr or ""):
            is_prose = True
        if any(p in (lowv or lowtxt) for p in ("must", "never", "requires", "should", "must not", "refuse")):
            is_prose = True

        # Confidence assignment
        if is_prose and not it.get("invariants_from_spec"):
            it["confidence"] = "low"
            it["inferred_from_prose"] = True
            # Explainability metadata for prose inference
            it.setdefault("meta", {})
            it["meta"].setdefault("source", "inferred")
            it["meta"].setdefault("justification", "heuristic_prose_keyword_match")
            it["meta"].setdefault("justification_ptr", it.get('ptr'))
            it["meta"].setdefault("inference_type", "heuristic")
            it["meta"].setdefault("tier", "C")
            # Confidence provenance for auditability
            it["confidence_meta"] = {"source": "heuristic:prose", "justification": "heuristic_prose_keyword_match"}
            # source excerpt hash for provenance
            excerpt_text = str(value) if value is not None else str(text or "")
            excerpt = excerpt_text[:512]
            it["evidence"]["source_excerpt_hash"] = hashlib.sha256(excerpt.encode()).hexdigest()[:12]
        else:
            # Derived from explicit fields/invariants/instructions
            if it.get("invariants_from_spec"):
                it["confidence"] = "high"
                it["confidence_meta"] = {"source": "invariant", "justification": "invariant_present"}
            elif "/instructions" in (ptr or "") or "/invariants" in (ptr or ""):
                it["confidence"] = "high"
                it["confidence_meta"] = {"source": "instruction", "justification": "explicit_instruction_or_invariant"}
            else:
                it["confidence"] = "medium"
                # Attach explainability for deterministic-derived confidence
                it.setdefault("meta", {})
                it["meta"].setdefault("source", "derived")
                it["meta"].setdefault("justification", "explicit_fields")
                it["meta"].setdefault("inference_type", "structural")
                it["meta"].setdefault("tier", "B")
                it["confidence_meta"] = {"source": "derived", "justification": "explicit_fields"}

        # Intent category detection (keyword-based)
        lowtxt = (text or "").lower()
        cat = "misc"
        for k, v in intent_map.items():
            if k in lowtxt:
                cat = v
                break
        # If pointer indicates governance
        if "/governance" in (ptr or ""):
            cat = "governance"
        it["intent_category"] = cat
        # Add a short quote for human consumption when available
        try:
            excerpt_text = str(value) if value is not None else str(text or "")
            if excerpt_text:
                it["evidence"]["quote"] = excerpt_text.strip()[:200]
        except Exception:
            pass

        # Derive an actionable imperative `action` string from the item text/claim
        try:
            import re

            def _create_action(txt: str) -> str:
                if not txt or not txt.strip():
                    return "Investigate unclear requirement and add an explicit invariant or test_ref."
                s = txt.strip()
                low = s.lower()
                # Determinism-specific actionable template
                if "determin" in low:
                    return "Verify build determinism by running repeated builds and comparing artifacts for bitwise identity."
                # Refusal / forbid templates
                if any(k in low for k in ("must not", "never", "refuse", "no-touch", "no touch")):
                    return f"Implement a refusal check to ensure the system rejects the operation described: \"{s}\"."
                # If starts with an imperative verb, preserve capitalization
                first = s.split()[0].lower()
                verbs = {"verify", "ensure", "confirm", "prevent", "reject", "refuse", "avoid", "maintain", "record", "attach", "add", "update", "remove", "delete", "create", "preserve", "lock", "authorize", "test", "run", "execute", "enforce", "log", "audit", "annotate", "synthesize", "generate", "persist", "validate", "confirm", "fix", "resolve", "implement", "design", "build"}
                if first in verbs:
                    return s[0].upper() + s[1:]
                # Replace modals with imperative
                s2 = re.sub(r"\bmust not\b", "do not", s, flags=re.I)
                s2 = re.sub(r"\bmust\b", "", s2, flags=re.I)
                s2 = re.sub(r"\bshould\b", "", s2, flags=re.I)
                s2 = s2.strip()
                if s2:
                    return f"Ensure {s2}"
                return f"Verify: {s}"

            base_txt = it.get("claim") or it.get("text") or it.get("value") or ""
            it["action"] = _create_action(str(base_txt))
        except Exception:
            it["action"] = "Investigate unclear requirement and add an explicit invariant or test_ref."

    return items


def ensure_item_fields(items: List[Dict]) -> List[Dict]:
    """Ensure required fields exist on every checklist item (idempotent)."""
    for it in items:
        # Treat missing or null values as absent
        if not it.get("confidence"):
            it["confidence"] = "medium"
        # Normalize confidence to canonical lowercase values
        if isinstance(it.get("confidence"), str):
            it["confidence"] = it["confidence"].lower()
        ev = it.setdefault("evidence", {})
        src = ev.get("source") or {}
        src.setdefault("ptr", it.get("ptr"))
        src.setdefault("line", None)
        ev["source"] = src
        it["evidence"] = ev
        if not it.get("inferred_from_prose"):
            it["inferred_from_prose"] = False
        if not it.get("intent_category"):
            it["intent_category"] = "misc"
        # Default readiness impact: 'blocks' | 'degrades' | 'neutral'
        if not it.get("readiness_impact"):
            it["readiness_impact"] = "neutral"
            # Determine priority deterministically: P0|P1|P2
            try:
                intent = (it.get("intent_category") or "").lower()
                blocking = bool(it.get("blocking"))
                severity = (it.get("severity") or "").lower()
                classification = (it.get("classification") or "").lower()
                if blocking or intent in ("determinism", "refusal", "safety"):
                    it["priority"] = "P0"
                elif it.get("invariants_from_spec") or classification in ("resolve-invariant", "resolve-cycle") or severity in ("high", "critical"):
                    it["priority"] = "P1"
                else:
                    it["priority"] = "P2"
            except Exception:
                it["priority"] = "P2"
        # Blocking: if there's no evidence quote or no source excerpt hash, mark as blocking (needs attention)
        try:
            has_quote = bool((it.get("evidence") or {}).get("quote"))
            has_hash = bool((it.get("evidence") or {}).get("source_excerpt_hash"))
            it["blocking"] = not (has_quote or has_hash)
        except Exception:
            it["blocking"] = True
    return items


def annotate_items_with_readiness_impact(items: List[Dict], readiness_results: Dict | None = None, spec: Dict | None = None) -> Dict:
        """Annotate items with `readiness_impact` and return a trace mapping.

        The trace maps failing readiness gates to the checklist item ids that
        are likely responsible, along with rationale and evidence references.

        This function does not change readiness logic; it only annotates items
        and produces a deterministic trace for authoring and CI.
        """
        trace = {}
        if not readiness_results or not isinstance(readiness_results, dict):
            return trace


        def generate_remediation_hint(item: Dict, spec: Dict | None = None) -> str:
            """Create a human-readable, deterministic remediation hint for a checklist item.

            Hints suggest which DSL section to add or enrich (e.g., sections, invariants, metadata).
            """
            ptr = item.get("ptr") or ""
            cat = item.get("intent_category") or "misc"
            text = (item.get("text") or "").strip()

            # Missing test refs advice
            if not item.get("test_refs"):
                return "Attach `test_refs` to this item so tests can be discovered (refer to tests_attached gate)."

            # Pointer-driven suggestions
            if "/metadata" in ptr:
                return "Add or enrich `metadata` (product_id, owner, version) to make provenance explicit."
            if "/invariants" in ptr or item.get("classification") == "resolve-invariant":
                return "Add explicit `invariants` expressing the requirement so it can be validated."
            if "/sections" in ptr or item.get("inferred_from_prose"):
                return "Clarify this `sections` entry: add explicit constraints, invariants, or a linked test_ref."
            if "/instructions" in ptr:
                return "Add deterministic `instructions` or break into smaller steps; attach `test_refs` where applicable."

            # Intent-driven fallbacks
            if cat == "safety":
                return "Turn this into an explicit `invariant` or governance policy under `governance` to increase confidence."
            if cat == "governance":
                return "Add a governance clause or policy section to express this enforcement as a rule."

            # Generic fallback
            return "Clarify this item in `sections` or add explicit `invariants`/`metadata` so it becomes high-confidence."


        def annotate_items_with_remediation(items: List[Dict], spec: Dict | None = None) -> List[Dict]:
            """Annotate items in-place with `remediation_hint` when confidence != 'high'.

            Returns the items list (idempotent).
            """
            for it in items:
                # Only add hints when item is not high confidence
                if (it.get("confidence") or "") != "high":
                    try:
                        it["remediation_hint"] = generate_remediation_hint(it, spec)
                    except Exception:
                        it["remediation_hint"] = "Consider clarifying this item (add invariants, metadata or tests)."
            return items





        results = readiness_results.get("results") or {}

        # Pre-index items by simple heuristics
        id_to_item = {it.get("id"): it for it in items}

        def _select_for_tests_attached():
            # Use the contract validator to find missing test refs deterministically
            try:
                from shieldcraft.verification.checklist_test_contract import validate_test_contract
                violations = validate_test_contract(items)
                ids = [v.get("id") for v in violations]
                if ids:
                    return ids, "missing_test_refs"
            except Exception:
                pass
            # Fallback: items with empty test_refs
            ids = [it.get("id") for it in items if not it.get("test_refs")]
            return ids, "no_test_refs"

        def _select_by_intent(keywords):
            ids = []
            for it in items:
                txt = (it.get("text") or "").lower()
                if any(k in txt for k in keywords) or it.get("intent_category") in keywords:
                    ids.append(it.get("id"))
            return ids

        for gate in sorted(results.keys()):
            v = results[gate]
            if isinstance(v, dict) and not v.get("ok"):
                blocking = bool(v.get("blocking"))
                rationale = v.get("reason") or v.get("governance") or "failed_gate"
                item_ids = []
                evidence_refs = []

                # Gate-specific heuristics
                if gate == "tests_attached":
                    ids, reason = _select_for_tests_attached()
                    rationale = f"tests_attached:{reason}"
                    item_ids = ids
                elif gate == "determinism_replay":
                    ids = _select_by_intent(["determinism"])
                    if not ids:
                        ids = sorted([it.get("id") for it in items if "determin" in (it.get("text") or "").lower()])
                    item_ids = ids
                elif gate == "spec_fuzz_stability":
                    ids = _select_by_intent(["governance"]) or sorted([it.get("id") for it in items if it.get("relevance_reason") == "dependency"]) or []
                    item_ids = ids
                elif gate == "persona_no_veto":
                    ids = _select_by_intent(["refusal", "safety"]) or []
                    item_ids = ids
                else:
                    # Generic fallback: pick items applicable to READY or first item
                    ids = [it.get("id") for it in items if "READY" in (it.get("applicable_states") or [])]
                    if not ids:
                        ids = sorted([it.get("id") for it in items])[:1]
                    item_ids = ids

                # Ensure deterministic non-empty mapping per acceptance criteria
                if not item_ids and items:
                    item_ids = [sorted([it.get("id") for it in items])[0]]

                # Collect evidence refs (source_excerpt_hash) when available
                for iid in item_ids:
                    it = id_to_item.get(iid)
                    if it:
                        h = (it.get("evidence") or {}).get("source_excerpt_hash")
                        if h:
                            evidence_refs.append(h)
                        # Annotate item readiness impact (blocks > degrades > neutral)
                        current = it.get("readiness_impact") or "neutral"
                        new = "blocks" if blocking else "degrades"
                        if current == "blocks":
                            pass
                        elif current == "degrades" and new == "blocks":
                            it["readiness_impact"] = "blocks"
                        elif current == "neutral":
                            it["readiness_impact"] = new

                trace[gate] = {
                    "blocking": blocking,
                    "reason": rationale,
                    "item_ids": sorted(item_ids),
                    "evidence_refs": sorted(set(evidence_refs)),
                }

        return trace
