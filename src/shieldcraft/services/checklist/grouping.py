def group_items(items):
    """
    Hierarchical deterministic grouping by:
    1) classification (core, dependency, invariant, bootstrap, module)
    2) severity (critical, high, medium, low)
    3) section (from spec sections)

    Output format:
    {
      "<group_key>": {
          "items":[...],
          "order_key": (classification_rank, severity_rank, section)
      }
    }

    Guarantees deterministic ordering.
    """
    out = {}

    # Rank order for deterministic sorting
    classification_rank = {
        "bootstrap": 0,
        "core": 1,
        "dependency": 2,
        "invariant": 3,
        "module": 4
    }

    severity_rank = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3
    }

    for it in items:
        c = it.get("classification", "core")
        s = it.get("severity", "low")
        section = it.get("section", "default")

        # Hierarchical group key: classification.severity.section
        grp = f"{c}.{s}.{section}"

        if grp not in out:
            out[grp] = {
                "items": [],
                "order_key": (
                    classification_rank.get(c, 99),
                    severity_rank.get(s, 99),
                    section
                )
            }
        out[grp]["items"].append(it)

    # Sort items deterministically inside each group
    for grp in out.values():
        grp["items"] = sorted(
            grp["items"],
            key=lambda x: (x.get("order_rank", 999), x.get("id", ""))
        )

    return out
