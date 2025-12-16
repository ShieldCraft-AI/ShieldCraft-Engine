"""Checklist context for recording gate events during compilation.

This is a lightweight, thread-safe recording object intended for plumbing
purposes only. Recording events MUST NOT change runtime control flow; it is
purely observational and used to collect gate outcomes for later emission
into checklist artifacts or logs.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from threading import Lock
from typing import Any, Dict, List, Optional


@dataclass
class ChecklistEvent:
    gate_id: str
    phase: str
    outcome: str
    message: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None


class ChecklistContext:
    """Thread-safe context that records checklist-related gate events.

    Usage: context.record_event(gate_id, phase, outcome, message=None, evidence=None)
    """

    def __init__(self) -> None:
        self._events: List[ChecklistEvent] = []
        self._lock = Lock()

    def record_event(self, gate_id: str, phase: str, outcome: str, message: Optional[str] = None, evidence: Optional[Dict[str, Any]] = None) -> None:
        """Record a single gate event. This method is non-blocking and
        does not modify control flow; callers should not rely on side-effects."""
        evt = ChecklistEvent(gate_id=gate_id, phase=phase, outcome=outcome, message=message, evidence=evidence)
        with self._lock:
            self._events.append(evt)

    def get_events(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [asdict(e) for e in list(self._events)]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {"events": self.get_events()}


# Optional global context registration helpers (defensive; plumbing only)
_GLOBAL_CONTEXT: Optional[ChecklistContext] = None

def set_global_context(ctx: Optional[ChecklistContext]) -> None:
    global _GLOBAL_CONTEXT
    _GLOBAL_CONTEXT = ctx


def get_global_context() -> Optional[ChecklistContext]:
    return _GLOBAL_CONTEXT


def record_event_global(gate_id: str, phase: str, outcome: str, message: Optional[str] = None, evidence: Optional[Dict[str, Any]] = None) -> None:
    """Convenience: record event to the registered global context if present."""
    try:
        gc = get_global_context()
        if gc is not None:
            try:
                gc.record_event(gate_id, phase, outcome, message=message, evidence=evidence)
            except Exception:
                pass
    except Exception:
        pass
