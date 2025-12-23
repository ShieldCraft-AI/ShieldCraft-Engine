from __future__ import annotations
import hashlib
import re
from typing import List, Dict

KEYWORDS = [
    "must",
    "must not",
    "must never",
    "requires",
    "should",
    "refuse",
    "refusal",
    "unsafe",
    "no-touch",
    "no touch",
    "no safe"]


def _det_hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def _sentences(text: str) -> List[str]:
    # Deterministic splitting on punctuation and line breaks
    text = text.replace('\r\n', '\n')
    # Split on headings (lines ending with ':'), bullets, numbered lists
    lines = []
    for raw in text.split('\n'):
        raw = raw.strip()
        if not raw:
            continue
        # bullets
        m = re.match(r'^(?:[-*]\s+)(.+)', raw)
        if m:
            lines.append(m.group(1).strip())
            continue
        # numbered
        m = re.match(r'^(?:\d+\.|\d+\))\s*(.+)', raw)
        if m:
            lines.append(m.group(1).strip())
            continue
        # headings
        if raw.endswith(':') or (len(raw) < 80 and raw.upper() == raw):
            lines.append(raw.rstrip(':').strip())
            continue
        # split long paragraphs into sentences
        parts = re.split(r'(?<=[.!?])\s+', raw)
        for p in parts:
            p = p.strip()
            if p:
                lines.append(p)
    return lines


def interpret_spec(raw_input: str) -> List[Dict]:
    """Interpret free-text spec into a list of ChecklistItem v1 dicts.

    Always returns a non-empty list. Deterministic segmentation and IDs.

    ChecklistItem fields: id, claim, obligation, risk_if_false, confidence, evidence_ref
    """
    if raw_input is None:
        raw_input = ""
    text = str(raw_input)
    candidates = []

    pieces = _sentences(text)

    for i, p in enumerate(pieces):
        low = p.lower()
        # Determine obligation and confidence
        found_kw = any(kw in low for kw in KEYWORDS)
        confidence = "low"
        obligation = None
        risk = None
        if found_kw:
            # stronger confidence for explicit obligations
            confidence = "medium"
            obligation = p
            # heuristically extract risk phrases
            if "refuse" in low or "no-touch" in low or "no touch" in low or "unsafe" in low or "no safe" in low:
                risk = "unsafe_to_act"
        else:
            # make a claim if no explicit obligation
            obligation = p
            confidence = "low"

        cid = _det_hash(f"{i}:{p}")
        candidates.append({
            "id": cid,
            "claim": p,
            "obligation": obligation,
            "risk_if_false": risk,
            "confidence": confidence,
            "evidence_ref": {"ptr": "/interpreted", "excerpt_hash": _det_hash(p)}
        })

    # Ensure never empty: synthesize from first line if needed
    if not candidates:
        s = (text or "no content").strip()
        cid = _det_hash(s or "empty")
        candidates.append({
            "id": cid,
            "claim": s or "(no content)",
            "obligation": s or "(no content)",
            "risk_if_false": None,
            "confidence": "low",
            "evidence_ref": {"ptr": "/interpreted", "excerpt_hash": _det_hash(s or "empty")}
        })

    return candidates


# Backwards-compatible export of the lower-level raw interpreter
try:
    # import late to avoid circular imports during package import-time
    from .interpreter import interpret_raw_spec  # type: ignore
except Exception:
    # Best-effort: if the module isn't available during some import flows, ignore
    interpret_raw_spec = None

try:
    from .raw_interpreter import RawSpecInterpreter  # type: ignore
except Exception:
    RawSpecInterpreter = None
