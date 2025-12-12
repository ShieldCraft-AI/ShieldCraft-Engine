def dedupe_items(items):
    """
    Deduplicate by (ptr, text, canonical value json).
    Deterministic: keep first occurrence only.
    """
    seen = set()
    out = []
    for it in items:
        key = (it["ptr"], it["text"], str(it.get("value")))
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out
