import os
import json
from dataclasses import asdict, dataclass
from typing import List, Optional

# Locked artifact location for execution state
EXECUTION_STATE_DIR = "artifacts"
EXECUTION_STATE_FILENAME = "execution_state_v1.json"
ANNOTATIONS_FILENAME = "persona_annotations_v1.json"
EVENTS_FILENAME = "persona_events_v1.json"
EVENTS_HASH_FILENAME = "persona_events_v1.hash"


@dataclass
class ExecutionStateEntry:
    phase: str
    gate: str
    status: str  # start, ok, fail
    error_code: Optional[str] = None


def _state_file_path() -> str:
    d = EXECUTION_STATE_DIR
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, EXECUTION_STATE_FILENAME)


def emit_state(engine, phase: str, gate: str, status: str, error_code: Optional[str] = None) -> None:
    """Append a state entry and persist deterministically (no timestamps).

    This function is deterministic: entries are appended in the order
    of emission and written as a canonical JSON array with sorted keys.
    """
    if not hasattr(engine, "_execution_state_entries"):
        engine._execution_state_entries = []  # type: ignore

    entry = ExecutionStateEntry(phase=phase, gate=gate, status=status, error_code=error_code)
    engine._execution_state_entries.append(asdict(entry))
    # Persist deterministically
    path = _state_file_path()
    with open(path, "w") as f:
        json.dump(engine._execution_state_entries, f, indent=2, sort_keys=True)


def read_state() -> List[dict]:
    p = _state_file_path()
    if not os.path.exists(p):
        return []
    return json.loads(open(p).read())


def _annotations_path() -> str:
    d = EXECUTION_STATE_DIR
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, ANNOTATIONS_FILENAME)


def emit_persona_annotation(engine, persona_id: str, phase: str, message: str, severity: str = "info") -> None:
    """Deterministically append a persona annotation (ordered, no timestamps)."""
    if not hasattr(engine, "_persona_annotations"):
        engine._persona_annotations = []  # type: ignore
    entry = {
        "persona_id": persona_id,
        "phase": phase,
        "message": message,
        "severity": severity,
    }
    engine._persona_annotations.append(entry)
    p = _annotations_path()
    with open(p, "w") as f:
        json.dump(engine._persona_annotations, f, indent=2, sort_keys=True)


def read_persona_annotations() -> List[dict]:
    p = _annotations_path()
    if not os.path.exists(p):
        return []
    return json.loads(open(p).read())


def _events_path() -> str:
    d = EXECUTION_STATE_DIR
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, EVENTS_FILENAME)


def _events_hash_path() -> str:
    d = EXECUTION_STATE_DIR
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, EVENTS_HASH_FILENAME)


def _validate_event_schema(event: dict) -> None:
    """Lightweight, deterministic validation against persona_event_v1.schema.json.

    This enforces presence, types and forbids unknown fields without depending on
    an external JSON Schema runtime.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "..", "persona", "persona_event_v1.schema.json")
    try:
        schema = json.loads(open(schema_path).read())
    except Exception:
        # If schema missing, reject to be conservative
        raise RuntimeError("persona_event_schema_missing")

    required = schema.get("required", [])
    for k in required:
        if k not in event:
            raise RuntimeError(f"persona_event_missing_required:{k}")

    allowed = set(schema.get("properties", {}).keys())
    extra = set(event.keys()) - allowed
    if extra:
        raise RuntimeError(f"persona_event_unknown_fields:{sorted(list(extra))}")

    # Basic type checks
    props = schema.get("properties", {})
    for k, v in event.items():
        prop = props.get(k)
        if not prop:
            continue
        t = prop.get("type")
        if t == "string" and not isinstance(v, str):
            raise RuntimeError(f"persona_event_invalid_type:{k}")
        if k == "capability" and v not in ["annotate", "veto"]:
            raise RuntimeError("persona_event_invalid_capability")


def _write_events_and_hash(engine) -> None:
    path = _events_path()
    with open(path, "w") as f:
        json.dump(getattr(engine, "_persona_events", []), f, indent=2, sort_keys=True)

    # Compute deterministic hash over canonical representation (no whitespace variance)
    from shieldcraft.util.json_canonicalizer import canonicalize
    payload = canonicalize(getattr(engine, "_persona_events", []))
    import hashlib
    h = hashlib.sha256(payload.encode()).hexdigest()
    with open(_events_hash_path(), "w") as f:
        f.write(h)


def emit_persona_event(engine, persona_id: str, capability: str, phase: str, payload_ref: str, severity: str = "info") -> None:
    """Append a PersonaEvent and persist deterministically with a companion hash.

    PersonaEvent fields: persona_id, capability (annotate|veto), phase, payload_ref, severity
    """
    if not hasattr(engine, "_persona_events"):
        engine._persona_events = []  # type: ignore

    event = {
        "persona_id": persona_id,
        "capability": capability,
        "phase": phase,
        "payload_ref": payload_ref,
        "severity": severity,
    }
    # Validate against locked schema
    _validate_event_schema(event)

    engine._persona_events.append(event)
    _write_events_and_hash(engine)


def read_persona_events() -> List[dict]:
    p = _events_path()
    if not os.path.exists(p):
        return []
    return json.loads(open(p).read())


def read_persona_events_hash() -> str:
    p = _events_hash_path()
    if not os.path.exists(p):
        return ""
    return open(p).read().strip()
