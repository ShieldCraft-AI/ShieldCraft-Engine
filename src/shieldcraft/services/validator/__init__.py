"""
Instruction Validator (minimal runtime contract)

Contract (summary):
- A valid instruction spec must declare a non-empty `invariants` list.
- A valid instruction spec must include an `instructions` list; each instruction must include `id` and `type`.
- Instruction `id` values must be unique.
- Ambient state is forbidden: instruction payloads MUST NOT contain runtime keys such as
  `timestamp`, `now`, `random`, `rand`, `seed`, or `time`.

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
	def __init__(self, code: str, message: str, location: str | None = None):
		# Present a human-friendly message while preserving a machine-readable `code` field.
		# Use spaces in the stringified code for clearer logs and test matches.
		super().__init__(f"{code.replace('_', ' ')}: {message}")
		self.code = code
		self.message = message
		self.location = location

	def to_dict(self):
		return {"code": self.code, "message": self.message, "location": self.location}


# Frozen set of canonical validation error codes (do not generate dynamic codes)
MISSING_INVARIANTS = "missing_invariants"
INVARIANTS_NOT_SORTED = "invariants_not_sorted"
MISSING_INSTRUCTIONS = "missing_instructions"
INSTRUCTION_NOT_OBJECT = "instruction_not_object"
INSTRUCTION_MISSING_FIELDS = "instruction_missing_fields"
DUPLICATE_INSTRUCTION_ID = "duplicate_instruction_id"
AMBIENT_STATE = "ambient_state"
SPEC_NOT_DICT = "spec_not_dict"

VALIDATION_ERROR_CODES = (
	MISSING_INVARIANTS,
	INVARIANTS_NOT_SORTED,
	MISSING_INSTRUCTIONS,
	INSTRUCTION_NOT_OBJECT,
	INSTRUCTION_MISSING_FIELDS,
	DUPLICATE_INSTRUCTION_ID,
	AMBIENT_STATE,
	SPEC_NOT_DICT,
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

	invariants = spec.get("invariants")
	if not invariants or not isinstance(invariants, list):
		raise ValidationError("missing_invariants", "spec must declare a non-empty 'invariants' list", "/invariants")

	# Invariants ordering must be deterministic; require sorted invariants list.
	# Support invariants as a list of objects (with `id`) or simple strings.
	def _invariants_ids(inv_list):
		if all(isinstance(x, dict) and "id" in x for x in inv_list):
			return [x["id"] for x in inv_list]
		return inv_list

	if _invariants_ids(invariants) != sorted(_invariants_ids(invariants)):
		raise ValidationError(INVARIANTS_NOT_SORTED, "invariants list must be sorted deterministically", "/invariants")

	instructions = spec.get("instructions")
	if not instructions or not isinstance(instructions, list):
		raise ValidationError(MISSING_INSTRUCTIONS, "spec must include an 'instructions' list", "/instructions")

	ids: Set[str] = set()
	for i, instr in enumerate(instructions):
		if not isinstance(instr, dict):
			raise ValidationError(INSTRUCTION_NOT_OBJECT, "each instruction must be an object", f"/instructions/{i}")
		if "id" not in instr or "type" not in instr:
			raise ValidationError(INSTRUCTION_MISSING_FIELDS, "instruction missing required fields 'id' and 'type'", f"/instructions/{i}")
		if instr["id"] in ids:
			raise ValidationError(DUPLICATE_INSTRUCTION_ID, f"duplicate instruction id: {instr['id']}", f"/instructions/{i}")
		ids.add(instr["id"])

		# Ambient key detection
		ambient_found = _contains_ambient(instr)
		if ambient_found:
			raise ValidationError(AMBIENT_STATE, f"ambient state detected: {sorted(ambient_found)}", f"/instructions/{i}")

	# No additional soft checks here; this is intentionally minimal and deterministic.

__all__ = ["validate_spec_instructions", "ValidationError"]
