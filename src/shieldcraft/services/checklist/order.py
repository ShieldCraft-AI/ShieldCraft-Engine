def ordering_constraints(raw_items):
    """
    Adds ordering requirements:
    - metadata tasks must run before architecture tasks
    - architecture tasks before agents tasks
    - agents tasks before api tasks
    Deterministic symbolic constraints only.
    """
    constraints = []
    cat_order = ["meta", "arch", "agent", "api"]

    # derive category mapping
    for i, item in enumerate(raw_items):
        # Handle both dict items and constraint items
        if not isinstance(item, dict):
            continue

        c = None
        ptr = item.get("ptr", "")
        if ptr.startswith("/metadata"):
            c = "meta"
        elif ptr.startswith("/architecture"):
            c = "arch"
        elif ptr.startswith("/agents"):
            c = "agent"
        elif ptr.startswith("/api"):
            c = "api"
        if c:
            item["_cat"] = c

    # generate constraints
    for a, b in zip(cat_order, cat_order[1:]):
        constraints.append({
            "ptr": f"/_order/{b}",
            "text": f"Tasks in {b} must execute after {a}",
            "value": {"after": a, "before": b}
        })

    return constraints


def assign_order_rank(item):
    """
    Ranking rules (lower = earlier):
    1) critical severity
    2) high severity
    3) classification alphabetical
    4) ptr length
    5) text lexicographic
    """
    sev = item.get("severity")
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(sev, 3)

    cls = item.get("classification", "zzz")

    return (
        sev_rank,
        cls,
        len(item["ptr"]),
        item["ptr"],
        item["text"]
    )


def ensure_stable_order(items):
    """
    Ensure deterministic ordering of items.

    Sort by:
    1. Section order (from schema)
    2. Classification type (lex)
    3. Severity ranking: low < medium < high < critical
    4. ID (lex)

    Returns: sorted list of items
    """
    from .classify import classify_type
    from .sections import SECTION_ORDER

    # Build section order map
    section_order_map = {s: i for i, s in enumerate(SECTION_ORDER)}

    # Define severity order (higher priority first): critical, high, medium, low
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def sort_key(item):
        # Extract section from ptr
        ptr = item.get("ptr", "")
        if ptr and ptr.startswith("/"):
            parts = ptr.lstrip("/").split("/")
            section = parts[0] if parts else "misc"
        else:
            section = "misc"

        # Map section to order
        section_idx = section_order_map.get(section, 999)

        # Get classification type
        cls_type = classify_type(item)

        # Get severity ranking
        severity = item.get("severity", "medium")
        sev_rank = severity_order.get(severity, 1)

        # Get ID
        item_id = item.get("id", "")

        return (section_idx, cls_type, sev_rank, item_id)

    return sorted(items, key=sort_key)
