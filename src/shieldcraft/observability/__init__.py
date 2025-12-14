import os
import json
from dataclasses import asdict, dataclass
from typing import List, Optional

# Locked artifact location for execution state
EXECUTION_STATE_DIR = "artifacts"
EXECUTION_STATE_FILENAME = "execution_state_v1.json"


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
