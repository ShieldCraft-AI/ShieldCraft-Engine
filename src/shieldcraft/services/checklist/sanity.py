def sanity_check(items):
    """
    Guards:
    - No duplicate IDs
    - ptr must start with '/'
    - text must be non-empty
    - severity must be one of allowed
    Return filtered valid list.
    """
    allowed = {"critical", "high", "medium", "low"}
    seen_ids = set()
    out = []
    for it in items:
        if not it["ptr"].startswith("/"):
            continue
        if not it["text"].strip():
            continue
        if it["severity"] not in allowed:
            continue
        if it["id"] in seen_ids:
            continue
        seen_ids.add(it["id"])
        out.append(it)
    return out
