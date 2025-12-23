SECTION_ORDER = [
    "meta",
    "arch",
    "agent",
    "api",
    "gov",
    "misc",
]

SECTION_TITLES = {
    "meta": "Metadata",
    "arch": "Architecture",
    "agent": "Agents",
    "api": "API",
    "gov": "Governance",
    "misc": "Miscellaneous",
}


def ordered_sections(categories):
    return [c for c in SECTION_ORDER if c in categories]


def group_by_section(items):
    """
    Group items by top-level spec section derived from ptr prefix.

    Returns: {"<section_name>": [items...]}
    """
    grouped = {}

    for item in items:
        ptr = item.get("ptr", "")

        # Extract top-level section from ptr
        if not ptr or ptr == "/":
            section = "root"
        else:
            # Remove leading slash and get first segment
            parts = ptr.lstrip("/").split("/")
            section = parts[0] if parts else "root"

        if section not in grouped:
            grouped[section] = []
        grouped[section].append(item)

    # Sort items within each section by id
    for section in grouped:
        grouped[section] = sorted(grouped[section], key=lambda x: x.get("id", ""))

    return grouped
