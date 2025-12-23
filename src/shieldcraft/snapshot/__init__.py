"""Deterministic repo snapshot utilities (minimal internal snapshot mechanism).

Snapshot contract (v1):
- Inputs: repository root directory (string), optional exclude list of paths.
- Outputs: manifest JSON containing:
    - version: "v1"
    - files: list of {path: str (relative), sha256: str}
    - tree_hash: sha256 of the deterministic concatenation of "{path}:{sha256}" for files sorted by path
- Hash algorithm: SHA256 for file contents and tree hash
- Excluded paths: `.git`, `.venv`, `node_modules`, `artifacts/`, `.selfhost_outputs/` by default

This module provides:
- `generate_snapshot(repo_root='.')` -> manifest dict
- `write_snapshot(manifest, path=None)` -> writes canonical JSON to `artifacts/repo_snapshot.json` by default
- `validate_snapshot(path, repo_root='.')` -> compares manifest to current repo and returns dict with `ok` or raises `SnapshotError`

Determinism: manifest entries are sorted and canonicalized. No network access.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, List


# Frozen include/exclude constants (do not modify lightly)
SNAPSHOT_EXCLUDES = frozenset({".git", ".venv", "node_modules", "artifacts", ".selfhost_outputs", "dist", "build"})
SNAPSHOT_DEFAULT_INCLUDES = frozenset({"**"})
DEFAULT_EXCLUDES = SNAPSHOT_EXCLUDES
DEFAULT_SNAPSHOT_PATH = os.path.join("artifacts", "repo_snapshot.json")

# Lock hash algorithm
HASH_ALGORITHM = "sha256"

# Manifest schema version
MANIFEST_VERSION = "v1"
SUPPORTED_MANIFEST_VERSIONS = {MANIFEST_VERSION}


class SnapshotError(ValueError):
    def __init__(self, code: str, message: str, details: Dict = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details = details or {}


SNAPSHOT_MISSING = "snapshot_missing"
SNAPSHOT_MISMATCH = "snapshot_mismatch"
SNAPSHOT_INVALID = "snapshot_invalid"
SNAPSHOT_EXTERNAL_DEPRECATED = "external_deprecated"

# Human-readable frozen messages
MSG_SNAPSHOT_MISMATCH = "external sync artifact does not match internal snapshot"
MSG_SNAPSHOT_INVALID = "invalid snapshot file"
MSG_SNAPSHOT_MISSING = "snapshot file missing"
MSG_EXTERNAL_DEPRECATED = "external sync mode is deprecated and not allowed without override"


def _compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def generate_snapshot(repo_root: str = ".", excludes: List[str] = None) -> Dict:
    """Generate deterministic snapshot manifest for files under `repo_root`.

    Returns a dict with keys: version, files (sorted list), tree_hash
    """
    if excludes is None:
        excludes = set(DEFAULT_EXCLUDES)
    else:
        excludes = set(excludes) | set(DEFAULT_EXCLUDES)

    files = []
    # canonical traversal: walk sorted dirs and filenames, normalize paths
    for root, dirs, filenames in os.walk(repo_root, topdown=True):
        dirs[:] = [d for d in sorted(dirs) if d not in excludes]
        for fname in sorted(filenames):
            full = os.path.join(root, fname)
            # normalize and compute relative path
            rel_path = os.path.normpath(os.path.relpath(full, repo_root)).replace("\\", "/")
            # skip if any path segment is excluded
            if any(seg in excludes for seg in rel_path.split("/")):
                continue
            # skip snapshot artifact by default to avoid self-inclusion
            if rel_path == DEFAULT_SNAPSHOT_PATH or rel_path.endswith("/" + os.path.basename(DEFAULT_SNAPSHOT_PATH)):
                continue
            sha = _compute_sha256(full)
            size = os.path.getsize(full)
            files.append({"path": rel_path, "sha256": sha, "size": size})

    # sort files deterministically by path
    files.sort(key=lambda x: x["path"])

    # compute tree hash: concatenation of path:sha256
    agg = "".join(f"{f['path']}:{f['sha256']}" for f in files)
    tree_hash = hashlib.sha256(agg.encode()).hexdigest()

    manifest = {"version": MANIFEST_VERSION, "hash_algorithm": HASH_ALGORITHM, "files": files, "tree_hash": tree_hash}
    # manifest schema sanity checks
    _validate_manifest_structure(manifest)
    return manifest


def write_snapshot(manifest: Dict, path: str = None) -> str:
    """Write canonical snapshot manifest to disk. Returns path written."""
    if path is None:
        path = DEFAULT_SNAPSHOT_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # validate before writing
    _validate_manifest_structure(manifest)
    # canonical JSON: sort keys, indent 2
    with open(path, "w", encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return path


def validate_snapshot(path: str, repo_root: str = ".") -> Dict:
    """Validate current repo against snapshot manifest at `path`.

    Returns {'ok': True} on success or raises `SnapshotError` with details.
    """
    if not os.path.exists(path):
        raise SnapshotError(SNAPSHOT_MISSING, "snapshot file missing", {"path": path})
    try:
        with open(path, encoding='utf-8') as f:
            manifest = json.load(f)
    except (IOError, OSError, json.JSONDecodeError, ValueError) as e:
        raise SnapshotError(SNAPSHOT_INVALID, f"invalid snapshot file: {e}")

    # version guard
    ver = manifest.get("version")
    if ver not in SUPPORTED_MANIFEST_VERSIONS:
        raise SnapshotError(SNAPSHOT_INVALID, f"unsupported manifest version: {ver}", {"version": ver})

    _validate_manifest_structure(manifest)

    current = generate_snapshot(repo_root)
    if manifest.get("tree_hash") != current.get("tree_hash"):
        raise SnapshotError(SNAPSHOT_MISMATCH, "repo tree does not match snapshot", {
                            "expected": manifest.get("tree_hash"), "actual": current.get("tree_hash")})

    return {"ok": True}


def _validate_manifest_structure(manifest: Dict) -> None:
    # strict manifest schema validation
    if manifest.get("version") not in SUPPORTED_MANIFEST_VERSIONS:
        raise SnapshotError(SNAPSHOT_INVALID, "unsupported manifest version", {"version": manifest.get("version")})
    if manifest.get("hash_algorithm") != HASH_ALGORITHM:
        raise SnapshotError(
            SNAPSHOT_INVALID, "hash algorithm mismatch", {
                "expected": HASH_ALGORITHM, "found": manifest.get("hash_algorithm")})
    if "files" not in manifest or not isinstance(manifest.get("files"), list):
        raise SnapshotError(SNAPSHOT_INVALID, "manifest 'files' must be a list")
    paths = set()
    for f in manifest.get("files", []):
        if "path" not in f or "sha256" not in f or "size" not in f:
            raise SnapshotError(SNAPSHOT_INVALID, "manifest file entries must include 'path','sha256','size'")
        if f["path"] in paths:
            raise SnapshotError(SNAPSHOT_INVALID, "duplicate path in manifest: %s" % f["path"])
        paths.add(f["path"])


def diff_snapshots(a: Dict, b: Dict) -> Dict:
    """Return deterministic diff between two manifests.

    Returns dict: {added: [paths], removed: [paths], changed: [{path, before, after}]}
    """
    _validate_manifest_structure(a)
    _validate_manifest_structure(b)

    amap = {f["path"]: f for f in a.get("files", [])}
    bmap = {f["path"]: f for f in b.get("files", [])}

    added = sorted([p for p in bmap.keys() if p not in amap])
    removed = sorted([p for p in amap.keys() if p not in bmap])
    changed = []
    for p in sorted(set(amap.keys()).intersection(bmap.keys())):
        if amap[p]["sha256"] != bmap[p]["sha256"] or amap[p]["size"] != bmap[p]["size"]:
            changed.append({"path": p, "before": amap[p], "after": bmap[p]})

    return {"added": added, "removed": removed, "changed": changed}


__all__ = [
    "generate_snapshot",
    "write_snapshot",
    "validate_snapshot",
    "DEFAULT_SNAPSHOT_PATH",
    "_validate_manifest_structure",
    "diff_snapshots",
    "SnapshotError",
    "SNAPSHOT_MISMATCH",
    "SNAPSHOT_MISSING",
    "SNAPSHOT_INVALID",
]
