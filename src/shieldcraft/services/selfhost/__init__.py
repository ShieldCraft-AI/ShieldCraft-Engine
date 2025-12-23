"""Self-hosting helpers and constants.

Defines the allowed artifact prefixes and small helpers to verify artifact emission
is constrained to the expected directories and filenames.
"""
from typing import Iterable

# Allowed output prefixes within the self-host output directory. These are
# relative paths (no leading slash) and specify directories that self-host
# is permitted to write into.
ALLOWED_SELFHOST_PREFIXES = (
    "bootstrap/",
    "modules/",
    "fixes/",
    "cycles/",
    "integration/",
    "__init__",
    "bootstrap_manifest.json",
    "manifest.json",
    "summary.json",
    "errors.json",
)


def is_allowed_selfhost_path(path: str, prefixes: Iterable[str] = ALLOWED_SELFHOST_PREFIXES) -> bool:
    """Return True if `path` is allowed to be emitted by self-host.

    `path` should be a relative path (no leading slash) and must start with
    one of the allowed prefixes or be exactly one of the allowed filenames.
    """
    if path in prefixes:
        return True
    for p in prefixes:
        if path.startswith(p):
            return True
    return False


def load_artifact_manifest():
    """Load canonical artifact manifest from disk (frozen contract file)."""
    import json
    from pathlib import Path
    p = Path(__file__).parent / "artifact_manifest.json"
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"allowed_prefixes": list(ALLOWED_SELFHOST_PREFIXES), "allowed_files": []}


# Readiness marker
SELFHOST_READINESS_MARKER = "SELFHOST_READY_V1"

# Engine version for provenance headers (bumped manually as part of releases)
ENGINE_VERSION = "0.1.0"

# Allowed top-level spec keys that self-host may consume
ALLOWED_SELFHOST_INPUT_KEYS = frozenset({"$schema",
                                         "canonical_spec_hash",
                                         "metadata",
                                         "model",
                                         "sections",
                                         "invariants",
                                         "instructions",
                                         "codegen_targets",
                                         "execution",
                                         "pointer_map"})


def provenance_header(spec_fingerprint: str, snapshot_hash: str | None, engine_version: str = ENGINE_VERSION) -> str:
    """Return a deterministic provenance header string to prefix emitted artifacts.

    This should be stable across runs and contain only deterministic values.
    """
    lines = [
        f"# engine_version: {engine_version}",
        f"# spec_fingerprint: {spec_fingerprint}",
        f"# snapshot_hash: {snapshot_hash or 'unknown'}",
    ]
    return "\n".join(lines) + "\n\n"


# Self-build constants
SELFBUILD_OUTPUT_DIR = "artifacts/self_build"
# Artifacts that must match bitwise for a successful self-build
SELFBUILD_BITWISE_ARTIFACTS = ("repo_snapshot.json", "bootstrap_manifest.json")

# Baseline storage (locked path)
SELFBUILD_BASELINE_DIR = "artifacts/self_build/baseline"
DEFAULT_BASELINE_NAME = "v1"

# Allowlist file (versioned)
BASELINE_ALLOWLIST_FILENAME = "baseline_allowlist_v1.json"


def load_baseline_allowlist(baseline_dir: str) -> dict:
    import json
    from pathlib import Path
    p = Path(baseline_dir) / BASELINE_ALLOWLIST_FILENAME
    if not p.exists():
        return {"version": 1, "allowed_diffs": []}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"version": 1, "allowed_diffs": []}


def is_allowed_diff(baseline_dir: str, rel_path: str) -> bool:
    data = load_baseline_allowlist(baseline_dir)
    allowed = set(data.get("allowed_diffs", []))
    return rel_path in allowed


def provenance_header_extended(
        spec_fingerprint: str,
        snapshot_hash: str | None,
        previous_snapshot: str | None = None,
        build_depth: int = 0,
        engine_version: str = ENGINE_VERSION) -> str:
    """Extended provenance header including self-build lineage."""
    lines = [
        f"# engine_version: {engine_version}",
        f"# spec_fingerprint: {spec_fingerprint}",
        f"# snapshot_hash: {snapshot_hash or 'unknown'}",
        f"# previous_snapshot: {previous_snapshot or 'none'}",
        f"# build_depth: {build_depth}",
    ]
    return "\n".join(lines) + "\n\n"


def is_allowed_selfhost_input(spec: dict) -> bool:
    """Return True if `spec` contains only allowed top-level keys for self-host ingestion."""
    if not isinstance(spec, dict):
        return False
    extra = set(spec.keys()) - ALLOWED_SELFHOST_INPUT_KEYS
    # Allow a deterministic ingestion envelope produced by `ingest_spec` which
    # uses the keys `metadata` and `raw_input`. Only accept the envelope when
    # it was explicitly normalized (metadata.normalized == True) to avoid
    # relaxing the allowlist for arbitrary inputs.
    if len(extra) == 0:
        return True
    if extra == {"raw_input"}:
        md = spec.get("metadata")
        if isinstance(md, dict) and md.get("normalized") is True:
            return True
    return False
