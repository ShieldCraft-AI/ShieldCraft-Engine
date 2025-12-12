def collapse_items(items):
    """
    Collapse items with same ptr and same 'prefix' semantics.

    Rule:
    - If two items share ptr AND one text starts with the other's text, keep shorter text.
    - Always deterministic.
    """
    by_ptr = {}
    for it in items:
        p = it["ptr"]
        by_ptr.setdefault(p, []).append(it)

    out = []
    for p, group in by_ptr.items():
        group_sorted = sorted(group, key=lambda x: len(x["text"]))
        keep = []
        for g in group_sorted:
            if not any(g["text"].startswith(k["text"]) for k in keep if k != g):
                keep.append(g)
        out.extend(keep)

    return out
