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
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Set


class ValidationError(ValueError):
	"""Raised when instruction validation fails."""


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
		raise ValidationError("spec must be a dict")

	invariants = spec.get("invariants")
	if not invariants or not isinstance(invariants, list):
		raise ValidationError("missing invariants: spec must declare a non-empty 'invariants' list")

	instructions = spec.get("instructions")
	if not instructions or not isinstance(instructions, list):
		raise ValidationError("missing instructions: spec must include an 'instructions' list")

	ids: Set[str] = set()
	for instr in instructions:
		if not isinstance(instr, dict):
			raise ValidationError("each instruction must be a dict")
		if "id" not in instr or "type" not in instr:
			raise ValidationError("instruction missing required fields 'id' and 'type'")
		if instr["id"] in ids:
			raise ValidationError(f"duplicate instruction id: {instr['id']}")
		ids.add(instr["id"])

		# Ambient key detection
		ambient_found = _contains_ambient(instr)
		if ambient_found:
			raise ValidationError(f"ambient state detected in instruction {instr.get('id')}: {sorted(ambient_found)}")

	# No additional soft checks here; this is intentionally minimal and deterministic.

__all__ = ["validate_spec_instructions", "ValidationError"]
