def build_rollups(grouped):
    """
    Build deterministic rollups:
    - count per severity
    - count per classification
    - count per type (including dependency, invariant, cycle tasks)
    - total items
    - missing-items summary
    - derived count
    - by_category breakdown
    - missing_ptrs list

    Output:
    {
       "total": int,
       "total_items": int,
       "by_severity": {...},
       "by_category": {...},
       "by_classification": {...},
       "by_type": {...},
       "derived_count": int,
       "missing": [ids],
       "missing_ptrs": [ids]
    }
    """
    total = 0
    by_sev = {}
    by_cat = {}
    by_cls = {}
    by_type = {}
    derived_count = 0
    missing = []
    missing_ptrs = []

    for grp, data in grouped.items():
        for it in data["items"]:
            total += 1
            sev = it.get("severity", "low")
            cat = it.get("category", "core")
            cls = it.get("classification", "core")
            item_type = it.get("type", "task")

            by_sev[sev] = by_sev.get(sev, 0) + 1
            by_cat[cat] = by_cat.get(cat, 0) + 1
            by_cls[cls] = by_cls.get(cls, 0) + 1
            by_type[item_type] = by_type.get(item_type, 0) + 1
            
            if it.get("derived", False):
                derived_count += 1

            if "SPEC MISSING" in it.get("text", ""):
                missing.append(it.get("id", "unknown"))
            
            ptr = it.get("ptr")
            if ptr is None or ptr == "":
                missing_ptrs.append(it.get("id", "unknown"))

    # Add breakdown for special task types
    dependency_tasks = by_type.get("fix-dependency", 0)
    invariant_tasks = by_type.get("resolve-invariant", 0)
    cycle_tasks = by_type.get("resolve-cycle", 0)
    
    # Compute severity heatmap
    severity_heatmap = {
        "critical": by_sev.get("critical", 0),
        "high": by_sev.get("high", 0),
        "medium": by_sev.get("medium", 0),
        "low": by_sev.get("low", 0)
    }

    return {
        "total": total,
        "total_items": total,
        "by_severity": dict(sorted(by_sev.items())),
        "by_category": dict(sorted(by_cat.items())),
        "by_classification": dict(sorted(by_cls.items())),
        "by_type": dict(sorted(by_type.items())),
        "derived_count": derived_count,
        "dependency_tasks": dependency_tasks,
        "invariant_tasks": invariant_tasks,
        "cycle_tasks": cycle_tasks,
        "severity_heatmap": severity_heatmap,
        "missing": sorted(missing),
        "missing_ptrs": sorted(missing_ptrs)
    }
