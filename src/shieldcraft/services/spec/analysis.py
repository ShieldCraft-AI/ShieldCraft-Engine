"""DSL semantic analysis helpers.

Provides deterministic diagnostics about which top-level DSL sections are
present/empty and a lightweight classification based on current engine
validation behavior. This is intentionally conservative and non-invasive.
"""
from __future__ import annotations

from typing import Any, Dict
from copy import deepcopy

from shieldcraft.services.spec.schema_validator import validate_spec_against_schema
from shieldcraft.services.validator import validate_instruction_block, ValidationError


SECTION_KEYS = ("metadata", "model", "sections", "invariants", "instructions", "codegen_targets", "execution", "pointer_map")


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, (list, dict, str)) and len(v) == 0:
        return True
    return False


def classify_dsl_sections(spec: Dict[str, Any], schema_path: str) -> Dict[str, Dict[str, Any]]:
    """Return classification for each known DSL section.

    Output mapping for each key contains:
      - present: bool
      - empty: bool
      - schema_valid_with_current: bool
      - schema_valid_when_removed: bool
      - instruction_valid_when_removed: bool
      - classification: one of 'structural', 'semantic', 'deferred'

    The classification is derived deterministically based on whether schema
    and instruction validation succeed when the key is removed or emptied.
    """
    out: Dict[str, Dict[str, Any]] = {}

    try:
        orig_valid, _ = validate_spec_against_schema(spec, schema_path)
    except Exception:
        orig_valid = True

    for key in SECTION_KEYS:
        present = key in spec
        empty = _is_empty(spec.get(key))

        # Schema validity when removing the key
        s_no = deepcopy(spec)
        if key in s_no:
            s_no.pop(key)
        try:
            valid_no_key, _ = validate_spec_against_schema(s_no, schema_path)
        except Exception:
            valid_no_key = True

        # Instruction validation when removing the key
        try:
            try_instr = deepcopy(spec)
            if key in try_instr:
                try_instr.pop(key)
            validate_instruction_block(try_instr)
            instr_ok_no_key = True
        except ValidationError:
            instr_ok_no_key = False
        except Exception:
            instr_ok_no_key = True

        # Decide classification
        if not orig_valid and valid_no_key:
            # Presence of this key (or its type) causes schema failure -> semantic
            classification = "semantic"
        elif not valid_no_key:
            # Removing the key breaks schema -> structural (must exist)
            classification = "structural"
        else:
            # Neither presence nor absence affects validation -> deferred
            classification = "deferred"

        out[key] = {
            "present": present,
            "empty": empty,
            "schema_valid_with_current": orig_valid,
            "schema_valid_when_removed": valid_no_key,
            "instruction_valid_when_removed": instr_ok_no_key,
            "classification": classification,
        }

    return out
