"""
Instruction Validator (minimal runtime contract)

Contract (summary):
- A valid instruction spec must declare a non-empty `invariants` list.
- A valid instruction spec must include an `instructions` list; each instruction must include `id` and `type`.
- Instruction `id` values must be unique.
- Ambient state is forbidden: instruction payloads MUST NOT contain runtime keys such as
    `timestamp`, `now`, `random`, `rand`, `seed`, or `time`.

Validity vs Readiness:
- Validity: this module determines whether the spec is structurally and semantically
    valid for engine processing (instruction-level invariants and strictness policy).
- Readiness: operational checks (tests attached, determinism replay, persona vetoes)
    are evaluated separately by the readiness evaluator. A spec may be valid yet not ready.

Determinism: Validation is deterministic (pure function of `spec`). On violation, validation fails hard
by raising `ValueError` with a clear message identifying the violation.

This module provides a single convenience API `validate_spec_instructions(spec)`.

Note: This validator is intended to be the single enforcement gate for instruction-level
validation in the engine. Call this API from `Engine._validate_spec` to ensure a single,
deterministic validation behavior across all engine entry points.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Set


class ValidationError(ValueError):
    """Raised when instruction validation fails.

    Carries structured error information for deterministic reporting:
    - code: machine-readable error code
    - message: human message
    - location: JSON Pointer-like location string (or None)

    Use `to_dict()` to serialize deterministically.
    """

    def __init__(self, code: str, message: str, location: str | None = None, details: dict | None = None):
        super().__init__(f"{code.replace('_', ' ')}: {message}")
        self.code = code
        self.message = message
        self.location = location
        self.details = details

    def to_dict(self):
        out = {"code": self.code, "message": self.message, "location": self.location}
        if getattr(self, "details", None) is not None:
            out["details"] = self.details
        return out


# Frozen set of canonical validation error codes (do not generate dynamic codes)
MISSING_INVARIANTS = "missing_invariants"
INVARIANTS_NOT_SORTED = "invariants_not_sorted"
MISSING_INSTRUCTIONS = "missing_instructions"
INSTRUCTION_NOT_OBJECT = "instruction_not_object"
INSTRUCTION_MISSING_FIELDS = "instruction_missing_fields"
DUPLICATE_INSTRUCTION_ID = "duplicate_instruction_id"
AMBIENT_STATE = "ambient_state"
SPEC_NOT_DICT = "spec_not_dict"
SECTIONS_EMPTY = "sections_empty"
MODEL_EMPTY = "model_empty"
INVARIANTS_EMPTY = "invariants_empty"

VALIDATION_ERROR_CODES = (
    MISSING_INVARIANTS,
    INVARIANTS_NOT_SORTED,
    MISSING_INSTRUCTIONS,
    INSTRUCTION_NOT_OBJECT,
    INSTRUCTION_MISSING_FIELDS,
    DUPLICATE_INSTRUCTION_ID,
    AMBIENT_STATE,
    SPEC_NOT_DICT,
    SECTIONS_EMPTY,
    MODEL_EMPTY,
    INVARIANTS_EMPTY,
)


_AMBIENT_KEYS = {"timestamp", "now", "random", "rand", "seed", "time"}


def _contains_ambient(obj: Any) -> Iterable[str]:
    """Recursively search `obj` for ambient keys; yield found keys.

    Deterministic and simple: inspects dict keys only.
    """
    found = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _AMBIENT_KEYS:
                found.add(k)
            # Recurse
            found |= set(_contains_ambient(v))
    elif isinstance(obj, list):
        for item in obj:
            found |= set(_contains_ambient(item))
    return found


def validate_spec_instructions(spec: Dict[str, Any]) -> None:
    """Validate instruction-level invariants in `spec`.

    Raises `ValidationError` (subclass of `ValueError`) on any violation.
    """
    if not isinstance(spec, dict):
        raise ValidationError(SPEC_NOT_DICT, "spec must be a dict")

    # If either `invariants` or `instructions` is present, require the other to be
    # present as well to preserve the legacy instruction-style contract. If neither
    # is present (canonical spec form), skip legacy instruction checks.
    invariants = spec.get("invariants")
    instructions = spec.get("instructions")

    if invariants is None and instructions is None:
        # Canonical / sections-based spec: nothing more to validate here.
        return

    # If we reach here, at least one legacy block is present — require both.
    if invariants is None:
        raise ValidationError(MISSING_INVARIANTS, "spec must declare a non-empty 'invariants' list", "/invariants")
    # Allow canonical specs that use `sections` + `invariants` (no legacy
    # `instructions` block). If `instructions` is missing but `sections` exists
    # treat this as a canonical spec with invariants and skip requiring
    # `instructions`.
    if instructions is None:
        if "sections" not in spec:
            raise ValidationError(MISSING_INSTRUCTIONS, "spec must include an 'instructions' list", "/instructions")

    # Validate invariants structure
    if not isinstance(invariants, list) or len(invariants) == 0:
        raise ValidationError(MISSING_INVARIANTS, "spec must declare a non-empty 'invariants' list", "/invariants")

    # Invariants ordering must be deterministic; require sorted invariants list.
    # Support invariants as a list of objects (with `id`) or simple strings.
    def _invariants_ids(inv_list):
        if all(isinstance(x, dict) and "id" in x for x in inv_list):
            return [x["id"] for x in inv_list]
        return inv_list

    if _invariants_ids(invariants) != sorted(_invariants_ids(invariants)):
        raise ValidationError(INVARIANTS_NOT_SORTED, "invariants list must be sorted deterministically", "/invariants")

    # Validate instructions structure (only if present)
    if instructions is None:
        return
    if not isinstance(instructions, list):
        raise ValidationError(MISSING_INSTRUCTIONS, "spec must include an 'instructions' list", "/instructions")

    ids: Set[str] = set()
    for i, instr in enumerate(instructions):
        if not isinstance(instr, dict):
            raise ValidationError(INSTRUCTION_NOT_OBJECT, "each instruction must be an object", f"/instructions/{i}")
        if "id" not in instr or "type" not in instr:
            raise ValidationError(
                INSTRUCTION_MISSING_FIELDS,
                "instruction missing required fields 'id' and 'type'",
                f"/instructions/{i}")
        if instr["id"] in ids:
            raise ValidationError(
                DUPLICATE_INSTRUCTION_ID,
                f"duplicate instruction id: {instr['id']}",
                f"/instructions/{i}")
        ids.add(instr["id"])

        # Ambient key detection
        ambient_found = _contains_ambient(instr)
        if ambient_found:
            raise ValidationError(
                AMBIENT_STATE,
                f"ambient state detected: {sorted(ambient_found)}",
                f"/instructions/{i}")

    # No additional soft checks here; this is intentionally minimal and deterministic.


__all__ = ["validate_spec_instructions", "ValidationError"]


def validate_instruction_block(spec: Dict[str, Any]) -> None:
    """Public, named entrypoint for instruction validation.

    This is the canonical name for validation and should be used by all callers.
    It preserves backward compatibility with `validate_spec_instructions`.
    """
    return validate_spec_instructions(spec)


# Export the new canonical name
__all__ = ["validate_spec_instructions", "validate_instruction_block", "ValidationError"]
