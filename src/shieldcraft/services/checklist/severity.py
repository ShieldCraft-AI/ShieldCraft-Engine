def compute_severity(item):
    """
    Deterministic severity mapping with escalation logic.

    Escalation rules:
    - If invariants violated → escalate to 'high'
    - If missing dependency + blocking → escalate to 'critical'

    Base rules:
    - Missing field → 'critical'
    - ptr endswith '/required' → 'high'
    - classification == metadata → 'high'
    - classification == determinism → 'high'
    - ptr contains 'validate' → 'medium'
    - default → 'low'
    """
    text = item.get("text", "")
    ptr = item.get("ptr", "")
    cls = item.get("classification", "")

    # Escalation: invariants violated
    invariants = item.get("invariants_from_spec", [])
    if invariants:
        # If any invariants are present, escalate to high
        return "high"

    # Escalation: missing dependency + blocking
    depends_on = item.get("depends_on", [])
    is_blocking = item.get("meta", {}).get("blocking", False)
    if depends_on and is_blocking:
        return "critical"

    # Base severity rules
    if "SPEC MISSING" in text:
        return "critical"
    if ptr.endswith("/required"):
        return "high"
    if cls in ("metadata", "determinism"):
        return "high"
    if "validate" in text.lower():
        return "medium"
    return "low"
