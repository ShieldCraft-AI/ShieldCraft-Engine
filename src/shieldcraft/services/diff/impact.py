def score_change(ptr):
    """
    Deterministic weighting:
    - /metadata/* → 5
    - /features/* → 10
    - /rules_contract/rules → 15
    - default → 1
    """
    if ptr.startswith("/metadata/"):
        return 5
    if ptr.startswith("/features/"):
        return 10
    if ptr.startswith("/rules_contract/rules"):
        return 15
    return 1


def impact_summary(diff_report):
    """Calculate impact score from diff report."""
    score = 0
    for c in diff_report["changed"]:
        score += score_change(c["ptr"])
    for a in diff_report["added"]:
        score += score_change(a["ptr"])
    for r in diff_report["removed"]:
        score += score_change(r["ptr"])

    return {
        "diff_score": score,
        "changed_count": len(diff_report["changed"]),
        "added_count": len(diff_report["added"]),
        "removed_count": len(diff_report["removed"])
    }


def compute_evolution_impact(evolution):
    """
    Compute change-impact score for evolution.

    Args:
        evolution: Evolution dict from compute_evolution()

    Returns:
        Dict with evolution_impact_score
    """
    if not evolution:
        return {"evolution_impact_score": 0}

    score = 0

    # Score added pointers
    for ptr in evolution.get("added", []):
        score += score_change(ptr)

    # Score removed pointers
    for ptr in evolution.get("removed", []):
        score += score_change(ptr)

    # Score changed pointers (higher weight)
    for ptr in evolution.get("changed", []):
        score += score_change(ptr) * 2

    return {
        "evolution_impact_score": score,
        "added_count": len(evolution.get("added", [])),
        "removed_count": len(evolution.get("removed", [])),
        "changed_count": len(evolution.get("changed", []))
    }


def classify_impact(evolution):
    """
    Classify impact as minor, moderate, or major.

    Args:
        evolution: Evolution dict from compute_evolution()

    Returns:
        String: "minor" | "moderate" | "major"
    """
    if not evolution:
        return "minor"

    summary = evolution.get("summary", {})
    added = summary.get("added_count", 0)
    removed = summary.get("removed_count", 0)
    changed = summary.get("changed_count", 0)

    total_changes = added + removed + changed

    # Classification thresholds
    if total_changes == 0:
        return "minor"

    # Major: many changes or structural changes
    if removed > 5 or (added > 10 and changed > 5):
        return "major"

    # Moderate: several changes
    if total_changes > 5 or (added > 3 and changed > 2):
        return "moderate"

    # Minor: few changes
    return "minor"
