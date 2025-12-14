import os
import re
import stat

# Canonical governance artifacts (locked references)
REQUIRED_GOVERNANCE_ARTIFACTS = {
    "decision_log": "docs/decision_log.md",
    "operational_readiness": "docs/OPERATIONAL_READINESS.md",
    "contracts": "docs/CONTRACTS.md",
}


def _extract_version_from_text(text: str) -> str | None:
    """Scan text for common version keys and return the first match."""
    # Look for YAML-like keys: version: x.y.z or spec_version: x.y.z or engine_version: x.y.z
    for key in ("version", "spec_version", "engine_version"):
        m = re.search(rf"^{key}:\s*([0-9]+(?:\.[0-9]+)*)", text, flags=re.M)
        if m:
            return m.group(1)
    return None


def check_governance_presence(root: str = None, engine_major: int | None = None):
    """Check required governance artifacts exist, are immutable, and align versions.

    Raises RuntimeError with deterministic codes on failure.
    """
    if root is None:
        root = os.getcwd()

    for name, rel_path in REQUIRED_GOVERNANCE_ARTIFACTS.items():
        path = os.path.join(root, rel_path)
        if not os.path.exists(path):
            raise RuntimeError(f"governance_artifact_missing: {name}")
        # Ensure file mode has no write bits (immutability assertion)
        try:
            mode = os.stat(path).st_mode
        except Exception:
            raise RuntimeError(f"governance_artifact_unreadable: {name}")
        if mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
            raise RuntimeError(f"governance_artifact_writable: {name}")
        # Version alignment: where present in artifact, ensure major matches
        try:
            text = open(path, "r").read()
        except Exception:
            raise RuntimeError(f"governance_artifact_unreadable: {name}")

        ver = _extract_version_from_text(text)
        if ver and engine_major is not None:
            try:
                a_major = int(ver.split(".")[0])
            except Exception:
                raise RuntimeError(f"governance_artifact_version_invalid: {name}")
            if a_major != engine_major:
                raise RuntimeError(f"governance_version_mismatch: {name}")

    return True
