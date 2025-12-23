"""Release helpers: generate deterministic RELEASE_MANIFEST.json of frozen artifacts.

This is intentionally small and deterministic: it enumerates the frozen contracts and
computes SHA256 hashes for a manifest used during release candidate preparation.
"""
from __future__ import annotations

import json
import hashlib
import os

# Canonical list of frozen artifacts to include in release manifest
FROZEN_ARTIFACTS = [
    "src/shieldcraft/persona/persona_v1.schema.json",
    "src/shieldcraft/persona/persona_event_v1.schema.json",
    "src/shieldcraft/services/selfhost/artifact_manifest.json",
    "src/shieldcraft/observability/__init__.py",
    "src/shieldcraft/persona/__init__.py",
]


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def generate_release_manifest(output: str = "RELEASE_MANIFEST.json") -> None:
    data = {"manifest_version": 1, "artifacts": []}
    for p in sorted(FROZEN_ARTIFACTS):
        if not os.path.exists(p):
            raise RuntimeError(f"frozen_artifact_missing: {p}")
        data["artifacts"].append({"path": p, "sha256": _sha256_of_file(p)})

    # Write deterministically
    with open(output, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)


def verify_release_manifest(manifest_path: str = "RELEASE_MANIFEST.json") -> bool:
    with open(manifest_path, encoding='utf-8') as f:
        data = json.load(f)
    for a in data.get("artifacts", []):
        path = a.get("path")
        expected = a.get("sha256")
        if _sha256_of_file(path) != expected:
            return False
    return True
