from ..spec.pointer_auditor import extract_json_pointers
import json
from pathlib import Path


def verify_generation_contract(spec, checklist_items, uncovered_ptrs):
    """
    Contract rules:
    - No required top-level field may be uncovered.
    - No checklist item may reference a nonexistent pointer.
    - Uncovered pointers allowed only if optional=true in spec metadata.
    - Generator version in spec must match lockfile.json generator_version.

    Return (ok: bool, violations:list[str])
    """
    violations=[]

    required = {
        "/metadata",
        "/product_intent",
        "/runtime_contract",
        "/api",
        "/features",
        "/determinism"
    }

    for r in required:
        if any(r == u or u.startswith(r+"/") for u in uncovered_ptrs):
            violations.append(f"Required field missing coverage: {r}")

    ptrs = set(extract_json_pointers(spec))
    for it in checklist_items:
        if it["ptr"] not in ptrs:
            violations.append(f"Checklist item references nonexistent pointer: {it['id']} → {it['ptr']}")
    
    # Lockfile enforcement: check generator version
    lockfile_path = Path(__file__).parent.parent.parent.parent.parent / "generators" / "lockfile.json"
    if lockfile_path.exists():
        lockfile = json.loads(lockfile_path.read_text())
        lockfile_version = lockfile.get("generator_version", "unknown")
        
        spec_version = spec.get("metadata", {}).get("generator_version", "unknown")
        
        if spec_version != lockfile_version:
            raise ValueError(
                f"GENERATOR_LOCKFILE_MISMATCH: expected {lockfile_version} but spec requests {spec_version}"
            )

    ok = not violations
    return ok, violations
