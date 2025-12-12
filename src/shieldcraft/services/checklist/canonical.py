def canonical_sort(items):
    """
    Canonically sort by:
    1) ptr (lexicographically)
    2) length of ptr
    3) text lexicographically
    4) stable value string
    """
    return sorted(
        items,
        key=lambda it: (
            it["ptr"],
            len(it["ptr"]),
            it["text"],
            str(it.get("value"))
        )
    )
