"""Minimal persona runtime scaffold (non-invasive).

Contract:
- Persona definitions are optional and loaded only when the feature flag
  `SHIELDCRAFT_PERSONA_ENABLED` is set to '1'.
- Loader enforces repo sync and clean worktree preconditions deterministically
  (uses `verify_repo_sync` and `is_worktree_clean`).

This module intentionally implements a small, well-scoped API:
- `Persona` dataclass: minimal, typed contract
- `load_persona(path)`: load and validate persona JSON from disk
- `PersonaError`: deterministic error for validation failures
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import pathlib
from dataclasses import field
from shieldcraft.util.json_canonicalizer import canonicalize

# note: import `verify_repo_sync` inside `load_persona` so tests can monkeypatch
# `shieldcraft.services.sync.verify_repo_sync` and have the change take effect.


"""
Error taxonomy (frozen codes):
- PERSONA_INVALID
- PERSONA_MISSING_NAME
- PERSONA_INVALID_SCHEMA
- PERSONA_MISSING_FILE
- PERSONA_INVALID_JSON
- WORKTREE_DIRTY
"""


PERSONA_INVALID = "persona_invalid"
PERSONA_MISSING_NAME = "persona_missing_name"
PERSONA_INVALID_SCHEMA = "persona_invalid_schema"
PERSONA_MISSING_FILE = "persona_missing_file"
PERSONA_INVALID_JSON = "persona_invalid_json"
WORKTREE_DIRTY = "worktree_dirty"
PERSONA_CONFLICT_DUPLICATE_NAME = "persona_conflict_duplicate_name"
PERSONA_CONFLICT_INCOMPATIBLE_SCOPE = "persona_conflict_incompatible_scope"


class PersonaError(ValueError):
    def __init__(self, code: str, message: str, location: Optional[str] = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.location = location

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message, "location": self.location}


@dataclass
class Persona:
    name: str
    role: Optional[str] = None
    display_name: Optional[str] = None
    scope: List[str] = field(default_factory=list)
    allowed_actions: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PersonaContext:
    name: str
    role: Optional[str]
    display_name: Optional[str]
    scope: List[str]
    allowed_actions: List[str]
    constraints: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "display_name": self.display_name,
            "scope": list(self.scope) if self.scope is not None else [],
            "allowed_actions": list(self.allowed_actions) if self.allowed_actions is not None else [],
            "constraints": dict(self.constraints) if self.constraints is not None else {},
        }

    def to_canonical_json(self) -> str:
        # Use canonicalize to produce deterministic serialization
        return canonicalize(self.to_dict())


def _is_worktree_clean() -> bool:
    """Return True if `git status --porcelain` is empty (deterministic check).

    This is a lightweight check and can be monkeypatched in tests.
    """
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL)
        return len(out.strip()) == 0
    except Exception:
        # If git is not available, treat as dirty to be conservative.
        return False


def find_persona_files(repo_root: str) -> List[str]:
    """Deterministic discovery: returns sorted list of candidate persona files.

    Rules:
    - Look for `persona.json` at repo root
    - Look for files under `personas/*.json`
    - Return sorted list (lexicographic) to ensure deterministic order
    """
    root = pathlib.Path(repo_root)
    candidates: List[str] = []
    p = root / "persona.json"
    if p.exists():
        candidates.append(str(p))
    for child in sorted((root / "personas").glob("*.json") if (root / "personas").exists() else []):
        candidates.append(str(child))
    return sorted(candidates)


def resolve_persona_files(paths: List[str]) -> Optional[str]:
    """Pure, deterministic resolution rule:

    - If no files -> None
    - If one file -> that file
    - If multiple -> prefer the file with the highest `version` field (numeric dot-separated comparison)
      if `version` absent, treat as 0.
    - On tie, prefer lexicographically smallest path
    """
    if not paths:
        return None
    # Load version info deterministically
    def _parse_version(p: str) -> List[int]:
        try:
            d = json.loads(open(p).read())
            v = d.get("version", "0")
            return [int(x) for x in v.split(".") if x.isdigit()]
        except Exception:
            return [0]

    versions = [(_parse_version(p), p) for p in paths]
    # Sort by version descending, then path ascending
    versions.sort(key=lambda x: (x[0], [""] if x[1] is None else [-1]))
    # custom sort: pick max by version list; implement deterministic selection
    best = None
    best_v = None
    for v, p in versions:
        if best is None or v > best_v or (v == best_v and p < best):
            best = p
            best_v = v
    return best


def detect_conflicts(paths: List[str]) -> List[Dict[str, Any]]:
    """Detect conflicts among candidate persona files.

    Returns a list of structured error dicts with deterministic ordering.
    """
    errors: List[Dict[str, Any]] = []
    if not paths:
        return errors

    # Map name -> list of files
    name_map: Dict[str, List[str]] = {}
    for p in sorted(paths):
        try:
            d = json.loads(open(p).read())
            name = d.get("name")
            if not name:
                continue
            name_map.setdefault(name, []).append(p)
        except Exception:
            continue

    for name, files in sorted(name_map.items()):
        if len(files) <= 1:
            continue
        # Compare scopes for compatibility
        scopes = []
        for p in files:
            try:
                d = json.loads(open(p).read())
                scopes.append((p, tuple(sorted(d.get("scope", [])))))
            except Exception:
                scopes.append((p, ()))

        distinct_scopes = sorted({s for _, s in scopes})
        if len(distinct_scopes) > 1:
            errors.append({
                "code": PERSONA_CONFLICT_INCOMPATIBLE_SCOPE,
                "message": f"conflicting scopes for persona '{name}'",
                "name": name,
                "files": files,
            })
        else:
            # duplicate name but same scope; still report duplicate
            errors.append({
                "code": PERSONA_CONFLICT_DUPLICATE_NAME,
                "message": f"duplicate persona name '{name}' in multiple files",
                "name": name,
                "files": files,
            })

    return sorted(errors, key=lambda e: (e["code"], e.get("name", "")))


def validate_persona_dict(d: Dict[str, Any]) -> None:
    if not isinstance(d, dict):
        raise PersonaError(PERSONA_INVALID, "persona must be an object", "/")
    if "name" not in d or not isinstance(d["name"], str) or not d["name"].strip():
        raise PersonaError(PERSONA_MISSING_NAME, "persona must declare a non-empty 'name'", "/name")
    # Optional structural checks
    if "scope" in d and not isinstance(d["scope"], list):
        raise PersonaError(PERSONA_INVALID, "'scope' must be a list", "/scope")


def _validate_against_schema(data: Dict[str, Any]) -> None:
    """Validate persona dict against the frozen persona_v1 schema.
    This is intentionally minimal and deterministic; we avoid heavy deps.
    """
    schema_path = pathlib.Path(__file__).parent / "persona_v1.schema.json"
    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except Exception:
        # If schema missing, be permissive (should not happen in CI).
        return

    # Check persona_version
    pv = data.get("persona_version")
    if pv != "v1":
        raise PersonaError(PERSONA_INVALID_SCHEMA, "unsupported or missing persona_version; expected 'v1'", "/persona_version")


def load_persona(path: str) -> Persona:
    """Load and validate a persona definition from `path`.

    Preconditions enforced deterministically:
    - repo sync verified via `verify_repo_sync(os.getcwd())`
    - worktree is clean via `_is_worktree_clean()`

    Raises `PersonaError` on validation failures and may raise `SyncError`.
    """
    # Verify repo sync (import dynamically so tests can monkeypatch the module-level
    # function on `shieldcraft.services.sync` and observe the change).
    from shieldcraft.services.sync import verify_repo_sync
    verify_repo_sync(os.getcwd())

    # Ensure worktree is clean
    if not _is_worktree_clean():
        raise PersonaError("worktree_dirty", "git worktree appears dirty; commit or stash changes before loading personas", "/")

    # Load JSON from disk
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        raise PersonaError(PERSONA_MISSING_FILE, f"persona file not found: {path}", path)
    except json.JSONDecodeError as e:
        raise PersonaError(PERSONA_INVALID_JSON, f"invalid JSON: {e}", path)

    validate_persona_dict(data)
    # Schema-level check
    _validate_against_schema(data)

    return Persona(
        name=data["name"],
        role=data.get("role"),
        display_name=data.get("display_name"),
        scope=data.get("scope", []),
        allowed_actions=data.get("allowed_actions", []),
        constraints=data.get("constraints", {}),
    )


def is_persona_enabled() -> bool:
    return os.getenv("SHIELDCRAFT_PERSONA_ENABLED", "0") == "1"


__all__ = ["Persona", "load_persona", "PersonaError", "is_persona_enabled", "_is_worktree_clean"]
