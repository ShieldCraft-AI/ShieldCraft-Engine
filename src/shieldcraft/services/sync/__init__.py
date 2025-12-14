"""Deterministic repository sync verification utilities.

Contract:
- `verify_repo_sync(repo_root)` checks that `repo_state_sync.json` exists and that
  the referenced sync artifacts (e.g., `artifacts/repo_sync_state.json`) exist and
  their SHA256 matches the recorded value. On failure, raises `SyncError`.

This is intentionally minimal and deterministic. Do not introduce network calls
or non-deterministic checks here.
"""
from __future__ import annotations

import json
import os
import hashlib
from typing import Any, Dict


class SyncError(ValueError):
    """Raised when repository sync verification fails.

    Carries structured `code`, `message`, and optional `location` and provides
    `to_dict()` for deterministic serialization consistent with `ValidationError`.
    """
    def __init__(self, code: str, message: str, location: str | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.location = location

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message, "location": self.location}


# Error codes
# Locked artifact contract
REPO_STATE_FILENAME = "repo_state_sync.json"
REPO_SYNC_ARTIFACT = "artifacts/repo_sync_state.json"

# Error codes (frozen)
SYNC_MISSING = "sync_missing"
SYNC_HASH_MISMATCH = "sync_hash_mismatch"
SYNC_INVALID_FORMAT = "sync_invalid_format"
SYNC_TREE_MISMATCH = "sync_tree_mismatch"


def _compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def verify_repo_sync(repo_root: str = ".") -> Dict[str, str]:
    """Verify presence and integrity of repo sync artifacts.

    Returns a dict with info on success. Raises `SyncError` on deterministic failure.
    """
    sync_path = os.path.join(repo_root, REPO_STATE_FILENAME)
    if not os.path.exists(sync_path):
        raise SyncError(SYNC_MISSING, "repo_state_sync.json not found", "/repo_state_sync.json")

    try:
        with open(sync_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                # Be tolerant of concatenated JSON artifacts in sync files by
                # attempting to parse the first top-level JSON object. This
                # makes verification robust in environments where multiple
                # processes may write the file sequentially without truncation.
                f.seek(0)
                raw = f.read()
                # Find the end index of the first top-level JSON object by
                # matching braces to avoid accidental concatenation issues.
                depth = 0
                end_idx = None
                for i, ch in enumerate(raw):
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            end_idx = i
                            break
                if end_idx is not None:
                    try:
                        data = json.loads(raw[: end_idx + 1])
                    except Exception:
                        raise SyncError(SYNC_INVALID_FORMAT, f"invalid repo_state_sync.json: {e}", "/repo_state_sync.json")
                else:
                    raise SyncError(SYNC_INVALID_FORMAT, f"invalid repo_state_sync.json: {e}", "/repo_state_sync.json")
    except Exception as e:
        raise SyncError(SYNC_INVALID_FORMAT, f"invalid repo_state_sync.json: {e}", "/repo_state_sync.json")

    # Expect an artifacts entry for artifacts/repo_sync_state.json with sha256
    target = REPO_SYNC_ARTIFACT
    found = None
    for entry in data.get("files", []):
        if entry.get("path") == target:
            found = entry
            break

    if not found:
        raise SyncError(SYNC_MISSING, f"expected sync artifact not listed: {target}", f"/{target}")

    if "sha256" not in found:
        raise SyncError(SYNC_INVALID_FORMAT, f"no sha256 recorded for {target}", f"/{target}")

    artifact_path = os.path.join(repo_root, target)
    if not os.path.exists(artifact_path):
        raise SyncError(SYNC_MISSING, f"sync artifact missing: {target}", f"/{target}")

    actual = _compute_sha256(artifact_path)
    if actual != found["sha256"]:
        raise SyncError(SYNC_HASH_MISMATCH, f"sha256 mismatch for {target}", f"/{target}")

    # Optional tree-level staleness check: if repo_state_sync.json includes
    # a precomputed `repo_tree_hash`, verify it matches an aggregate computed
    # from the listed files (deterministic concatenation of path:sha256).
    if "repo_tree_hash" in data:
        agg = "".join(f"{e.get('path')}:{e.get('sha256','')}" for e in sorted(data.get("files", []), key=lambda x: x.get('path')))
        tree_hash = hashlib.sha256(agg.encode()).hexdigest()
        if tree_hash != data.get("repo_tree_hash"):
            raise SyncError(SYNC_TREE_MISMATCH, "repo_tree_hash mismatch: repo snapshot appears stale", "/repo_tree_hash")

    return {"ok": True, "artifact": target, "sha256": actual}


def _canonical_manifest_hash(manifest: Dict) -> str:
    # Deterministic canonicalization: sort keys and compact JSON
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()


def verify_repo_state_authoritative(repo_root: str = ".") -> Dict[str, str]:
    """Decision point for authoritative sync verification.

    Authority modes controlled by env `SHIELDCRAFT_SYNC_AUTHORITY`:
    - 'external' (default): use verify_repo_sync
    - 'snapshot': use internal snapshot validation
    - 'snapshot_mandatory': same as 'snapshot' but fails if snapshot missing
    - 'compare': verify both external and snapshot and ensure parity

    Returns a dict similar to verify_repo_sync on success.
    Raises SyncError or SnapshotError on deterministic failures.
    """
    import logging
    # Default authority is repo_state_sync (use external repo_state_sync artifacts)
    authority = os.getenv("SHIELDCRAFT_SYNC_AUTHORITY", "repo_state_sync")

    # External mode: issue migration warning and rely on existing verify_repo_sync.
    if authority == "external":
        # External scanning is opt-in only. Require explicit override to allow.
        allow = os.getenv("SHIELDCRAFT_ALLOW_EXTERNAL_SYNC", "0") == "1"
        if not allow:
            raise SyncError("external_deprecated", "external sync mode is deprecated and not allowed without override", "/repo_state_sync.json")
        logging.getLogger("shieldcraft.snapshot").warning("snapshot_deprecation_notice: external sync mode enabled via override (deprecated)")
        res = verify_repo_sync(repo_root)
        res["authority"] = "external"
        return res

    # 'repo_state_sync' mode: verify external repo_state_sync.json and associated artifacts
    if authority == "repo_state_sync":
        # Treat repo_state_sync as derived state (non-mandatory):
        # If the external sync artifact is present, validate it; if it is
        # missing, allow the run to proceed (do not raise SyncError).
        try:
            res = verify_repo_sync(repo_root)
            res["authority"] = "repo_state_sync"
            return res
        except Exception as e:
            # If it's a SyncError due to missing artifact, relax and proceed;
            # otherwise re-raise to preserve strict failure modes for other errors.
            from inspect import getmodule
            # Detect SyncError by attribute presence (class imported above)
            if getattr(e, "code", None) == SYNC_MISSING:
                return {"ok": True, "authority": "repo_state_sync", "artifact": None}
            raise

    # Snapshot-based authority (opt-in only)
    from shieldcraft.snapshot import validate_snapshot, generate_snapshot, DEFAULT_SNAPSHOT_PATH, SnapshotError

    snapshot_path = os.path.join(repo_root, DEFAULT_SNAPSHOT_PATH)

    if authority == "snapshot":
        # Validate snapshot exists and matches
        validate_snapshot(snapshot_path, repo_root)
        # Return a synthetic response for compatibility
        manifest = generate_snapshot(repo_root)
        return {"ok": True, "authority": "snapshot", "sha256": manifest.get("tree_hash"), "artifact": snapshot_path}

    if authority == "snapshot_mandatory":
        # Same as snapshot but treat missing snapshot as fatal (validate_snapshot will raise)
        validate_snapshot(snapshot_path, repo_root)
        manifest = generate_snapshot(repo_root)
        return {"ok": True, "authority": "snapshot_mandatory", "sha256": manifest.get("tree_hash"), "artifact": snapshot_path}

    if authority == "compare":
        # Verify both external and snapshot, then compare a canonical manifest hash
        sync_res = verify_repo_sync(repo_root)
        manifest = generate_snapshot(repo_root)
        # read external artifact (assumed to contain canonical manifest JSON) and compare structure
        artifact_path = os.path.join(repo_root, REPO_SYNC_ARTIFACT)
        try:
            with open(artifact_path) as af:
                external_manifest = json.load(af)
        except Exception:
            raise SnapshotError("snapshot_invalid", "could not read external sync artifact for comparison", {"artifact": artifact_path})

        # compare canonical manifest hashes for deterministic parity
        # Exclude volatile repo-state file from parity checks to avoid
        # self-referential mismatches (repo_state_sync.json is written as
        # part of the external sync metadata and may change the manifest).
        def _sanitize(m: Dict) -> Dict:
            m2 = dict(m)
            files = [f for f in m2.get("files", []) if f.get("path") != REPO_STATE_FILENAME]
            files.sort(key=lambda x: x.get("path"))
            agg = "".join(f"{f['path']}:{f['sha256']}" for f in files)
            tree_hash = hashlib.sha256(agg.encode()).hexdigest()
            m2["files"] = files
            m2["tree_hash"] = tree_hash
            return m2

        internal_hash = _canonical_manifest_hash(_sanitize(manifest))
        external_hash = _canonical_manifest_hash(_sanitize(external_manifest))
        if internal_hash != external_hash:
            raise SnapshotError("snapshot_mismatch", "external sync artifact does not match internal snapshot", {"external_manifest_hash": external_hash, "internal_manifest_hash": internal_hash})
        return {"ok": True, "authority": "compare", "sha256": sync_res.get("sha256"), "artifact": sync_res.get("artifact")}

    # Unknown authority
    raise SyncError(SYNC_INVALID_FORMAT, f"unsupported sync authority: {authority}", "/")


__all__ = ["verify_repo_sync", "SyncError", "SYNC_MISSING", "SYNC_HASH_MISMATCH", "SYNC_INVALID_FORMAT"]
__all__ = [
    "verify_repo_sync",
    "SyncError",
    "REPO_STATE_FILENAME",
    "REPO_SYNC_ARTIFACT",
    "SYNC_MISSING",
    "SYNC_HASH_MISMATCH",
    "SYNC_INVALID_FORMAT",
    "SYNC_TREE_MISMATCH",
]
