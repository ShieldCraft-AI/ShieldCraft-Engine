"""
Multi-spec batch processor.
"""

import hashlib
import json
from shieldcraft.engine import Engine


def run_batch(spec_paths, schema_path):
    """
    Process multiple specs in batch.

    Args:
        spec_paths: List of paths to spec files
        schema_path: Path to schema file

    Returns:
        Dict with batch results
    """
    engine = Engine(schema_path)
    results = []

    for spec_path in sorted(spec_paths):
        try:
            result = engine.execute(spec_path)

            # Create summary
            summary = {
                "spec_path": spec_path,
                "success": result.get("type") != "schema_error",
                "checklist_count": len(result.get("checklist", {}).get("items", [])),
                "stable": result.get("stable", False)
            }

            if result.get("type") == "schema_error":
                summary["errors"] = result.get("details", [])

            results.append(summary)

        except Exception as e:
            results.append({
                "spec_path": spec_path,
                "success": False,
                "error": str(e)
            })

    # Compute batch hash for determinism
    batch_content = json.dumps(results, sort_keys=True)
    batch_hash = hashlib.sha256(batch_content.encode()).hexdigest()

    return {
        "results": results,
        "total": len(spec_paths),
        "successful": sum(1 for r in results if r.get("success", False)),
        "failed": sum(1 for r in results if not r.get("success", False)),
        "batch_hash": batch_hash
    }
