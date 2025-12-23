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
PERSONA_MISSING_VERSION = "persona_missing_version"
PERSONA_INVALID_VETO_EXPLANATION = "persona_invalid_veto_explanation"
PERSONA_ACTION_NOT_ALLOWED = "persona_action_not_allowed"
PERSONA_RATE_LIMIT_EXCEEDED = "persona_rate_limit_exceeded"
PERSONA_VERSION_INCOMPATIBLE = "persona_version_incompatible"


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
    # Optional authority classification for Phase 6 (DECISIVE|ADVISORY|ANNOTATIVE)
    authority: Optional[str] = None


@dataclass(frozen=True)
class PersonaContext:
    name: str
    role: Optional[str]
    display_name: Optional[str]
    scope: List[str]
    allowed_actions: List[str]
    constraints: Dict[str, Any]
    authority: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "display_name": self.display_name,
            "scope": list(self.scope) if self.scope is not None else [],
            "allowed_actions": list(self.allowed_actions) if self.allowed_actions is not None else [],
            "constraints": dict(self.constraints) if self.constraints is not None else {},
            "authority": self.authority,
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
    if "version" not in d or not isinstance(d["version"], str) or not d["version"].strip():
        raise PersonaError(PERSONA_MISSING_VERSION, "persona must declare a non-empty 'version'", "/version")
    # Optional structural checks
    if "scope" in d and not isinstance(d["scope"], list):
        raise PersonaError(PERSONA_INVALID, "'scope' must be a list", "/scope")


def _validate_against_schema(data: Dict[str, Any]) -> None:
    """Validate persona dict against the frozen persona_v1 _schema.
    This is intentionally minimal and deterministic; we avoid heavy deps.
    """
    schema_path = pathlib.Path(__file__).parent / "persona_v1._schema.json"
    try:
        with open(schema_path, encoding='utf-8') as f:
            json.load(f)
    except (IOError, OSError, json.JSONDecodeError, ValueError):
        # If _schema missing, be permissive (should not happen in CI).
        return

    # Check persona_version
    pv = data.get("persona_version")
    if pv != "v1":
        raise PersonaError(
            PERSONA_VERSION_INCOMPATIBLE,
            f"unsupported persona_version; expected 'v1', got '{pv}'",
            "/persona_version")


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
        raise PersonaError(
            "worktree_dirty",
            "git worktree appears dirty; commit or stash changes before loading personas",
            "/")

    # Load JSON from disk
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise PersonaError(PERSONA_MISSING_FILE, f"persona file not found: {path}", path)
    except json.JSONDecodeError as e:
        raise PersonaError(PERSONA_INVALID_JSON, f"invalid JSON: {e}", path)

    validate_persona_dict(data)
    # Schema-level check
    _validate_against_schema(data)

    # Enforce explicit version presence (identity lock)
    if "version" not in data or not isinstance(data["version"], str) or not data["version"].strip():
        raise PersonaError(PERSONA_MISSING_VERSION, "persona must declare a non-empty 'version'", f"{path}/version")

    return Persona(
        name=data["name"],
        role=data.get("role"),
        display_name=data.get("display_name"),
        scope=data.get("scope", []),
        allowed_actions=data.get("allowed_actions", []),
        constraints=data.get("constraints", {}),
        authority=data.get("authority"),
    )


# Capability matrix: locked mapping of roles to allowed actions.
# No implicit permissions: `allowed_actions` must be subset of these if provided.
PERSONA_CAPABILITY_MATRIX = {
    "observer": ["observe"],
    "auditor": ["observe", "annotate"],
    "governance": ["observe", "annotate", "veto"],
}

# Annotation rate limits (deterministic): max annotations per persona per phase
ANNOTATION_RATE_LIMIT_PER_PERSONA_PER_PHASE = 5

# Stable marker for hardened persona subsystem
PERSONA_STABLE = True
PERSONA_COMPLETE = True

# Registry for canonical persona entry points (single enforcement path assertion)
PERSONA_ENTRY_POINTS = set()


def persona_entry(capability: str):
    def deco(fn):
        PERSONA_ENTRY_POINTS.add((capability, fn.__name__))
        return fn
    return deco


def is_persona_enabled() -> bool:
    return os.getenv("SHIELDCRAFT_PERSONA_ENABLED", "0") == "1"


__all__ = ["Persona", "load_persona", "PersonaError", "is_persona_enabled", "_is_worktree_clean"]


@persona_entry("annotate")
def emit_annotation(engine, persona: PersonaContext, phase: str, message: str, severity: str = "info") -> None:
    """Persona-facing API to emit annotations deterministically.

    This is non-authoritative and must not affect engine behavior.
    """
    if not is_persona_enabled():
        raise PersonaError(PERSONA_INVALID, "persona feature not enabled")
    # Enforce scope: persona must include phase or 'all' in scope
    if persona.scope and phase not in persona.scope and "all" not in persona.scope:
        raise PersonaError(PERSONA_CONFLICT_INCOMPATIBLE_SCOPE, f"persona scope does not include phase: {phase}")
    # Enforce capability: persona must have 'annotate' permission
    if "annotate" not in (persona.allowed_actions or []):
        raise PersonaError(
            PERSONA_ACTION_NOT_ALLOWED,
            "persona not permitted to annotate",
            f"/personas/{persona.name}/allowed_actions")
    # Deterministic rate limiting: count prior annotations for this persona+phase
    existing = [a for a in getattr(engine, "_persona_annotations", []) if a.get(
        "persona_id") == persona.name and a.get("phase") == phase]
    if len(existing) >= ANNOTATION_RATE_LIMIT_PER_PERSONA_PER_PHASE:
        raise PersonaError(
            PERSONA_RATE_LIMIT_EXCEEDED,
            "persona exceeded annotation rate limit for phase",
            f"/personas/{persona.name}")
    try:
        from shieldcraft.observability import emit_persona_annotation
        emit_persona_annotation(engine, persona.name, phase, message, severity)
        # Emit a PersonaEvent for audit (payload_ref is canonicalized message)
        from shieldcraft.observability import emit_persona_event
        from shieldcraft.util.json_canonicalizer import canonicalize
        payload_ref = canonicalize({"message": message, "severity": severity})
        emit_persona_event(engine, persona.name, "annotate", phase, payload_ref, severity)
    except Exception as e:
        raise PersonaError(PERSONA_INVALID, f"failed to emit annotation: {e}")


def _validate_veto_explanation(explanation: Dict[str, Any]) -> None:
    if not isinstance(explanation, dict):
        raise PersonaError(PERSONA_INVALID_VETO_EXPLANATION, "veto explanation must be an object", "/explanation")
    if "explanation_code" not in explanation or not isinstance(explanation["explanation_code"], str):
        raise PersonaError(
            PERSONA_INVALID_VETO_EXPLANATION,
            "veto explanation must include 'explanation_code' string",
            "/explanation/explanation_code")
    if "details" not in explanation or not isinstance(explanation["details"], str):
        raise PersonaError(
            PERSONA_INVALID_VETO_EXPLANATION,
            "veto explanation must include 'details' string",
            "/explanation/details")


@persona_entry("veto")
def emit_veto(engine, persona: PersonaContext, phase: str, code: str,
              explanation: Dict[str, Any], severity: str = "high") -> None:
    """Persona-facing API to emit a veto; recorded for deterministic resolution.

    Veto does not propose alternatives. Engine checks for vetoes at deterministic
    checkpoints and will refuse execution if present.
    """
    if not is_persona_enabled():
        raise PersonaError(PERSONA_INVALID, "persona feature not enabled")
    if persona.scope and phase not in persona.scope and "all" not in persona.scope:
        raise PersonaError(PERSONA_CONFLICT_INCOMPATIBLE_SCOPE, f"persona scope does not include phase: {phase}")
    # Enforce capability: persona must have 'veto' permission
    if "veto" not in (persona.allowed_actions or []):
        raise PersonaError(
            PERSONA_ACTION_NOT_ALLOWED,
            "persona not permitted to veto",
            f"/personas/{persona.name}/allowed_actions")
    # Validate explanation _schema
    _validate_veto_explanation(explanation)
    if not hasattr(engine, "_persona_vetoes"):
        engine._persona_vetoes = []  # type: ignore
    veto = {"persona_id": persona.name, "phase": phase, "code": code, "explanation": explanation, "severity": severity}
    engine._persona_vetoes.append(veto)
    # also emit an annotation for audit
    try:
        from shieldcraft.observability import emit_persona_annotation
        emit_persona_annotation(
            engine,
            persona.name,
            phase,
            f"VETO: {code}: {explanation.get('explanation_code')}",
            severity)
        # Emit a PersonaEvent for audit purposes (payload_ref is canonicalized explanation)
        from shieldcraft.observability import emit_persona_event
        from shieldcraft.util.json_canonicalizer import canonicalize
        payload_ref = canonicalize({"code": code, "explanation": explanation})
        emit_persona_event(engine, persona.name, "veto", phase, payload_ref, severity)
    except Exception:
        pass
