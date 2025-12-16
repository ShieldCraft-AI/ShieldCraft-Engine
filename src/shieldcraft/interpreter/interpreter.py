from __future__ import annotations
import hashlib
import re
from typing import List
from shieldcraft.checklist.item_v1 import ChecklistItemV1


def _det_hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def _split_sections(text: str):
    # Split into blocks by headings (lines ending with ':'), numbered lists, or blank-line separated paragraphs
    lines = text.replace('\r\n', '\n').split('\n')
    sections = []
    cur_title = "intro"
    cur_body = []
    heading_re = re.compile(r'^\s*(.+?):\s*$')
    numbered_re = re.compile(r'^\s*\d+\.|^\s*\d+\)')
    bullet_re = re.compile(r'^\s*[-*]\s+')

    def flush():
        if cur_body or cur_title:
            sections.append((cur_title, "\n".join(cur_body).strip()))
    for ln in lines:
        if not ln.strip():
            # paragraph break
            if cur_body:
                flush()
                cur_title = ""
                cur_body = []
            continue
        m = heading_re.match(ln)
        if m:
            # new heading
            if cur_body:
                flush()
            cur_title = m.group(1).strip()
            cur_body = []
            continue
        # treat bullets/numbered as part of current section
        if numbered_re.match(ln) or bullet_re.match(ln):
            cur_body.append(ln.strip())
            continue
        # if line is uppercase-ish short, treat as heading
        if ln.strip() == ln.strip().upper() and len(ln.strip()) < 80:
            if cur_body:
                flush()
            cur_title = ln.strip()
            cur_body = []
            continue
        cur_body.append(ln)
    # final flush
    if cur_body or cur_title:
        sections.append((cur_title or "intro", "\n".join(cur_body).strip()))
    return sections


def interpret_raw_spec(text: str) -> List[ChecklistItemV1]:
    """Deterministically interpret raw spec text into ChecklistItemV1 list.

    Guarantees: never returns an empty list; emits at least one item per section.
    """
    if not text:
        text = "(no content)"
    sections = _split_sections(text)
    items: List[ChecklistItemV1] = []

    for idx, (title, body) in enumerate(sections):
        # create at least one claim per section
        body_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', body) if s.strip()]
        if not body_sentences:
            body_sentences = [title]
        # primary claim: combine title + first sentence
        claim = f"{title}: {body_sentences[0]}" if title and body_sentences[0] else (body_sentences[0] if body_sentences else title)
        cid = _det_hash(f"{idx}:{claim}")
        # determine confidence
        low_keywords = ("may", "might", "could", "possibly")
        high_keywords = ("must", "must not", "never", "always", "refuse", "unsafe")
        l = claim.lower()
        if any(k in l for k in high_keywords):
            conf = "HIGH"
        elif any(k in l for k in low_keywords):
            conf = "LOW"
        else:
            conf = "MEDIUM"
        # risk default
        risk = "unsafe or misleading change"
        if any(k in l for k in ("refuse", "no-touch", "no touch", "unsafe", "no safe")):
            risk = "unsafe_to_act"
        ev = {"ptr": "/interpreted", "excerpt_hash": _det_hash(claim)}
        items.append(ChecklistItemV1(id=cid, claim=claim, obligation=claim, risk_if_false=risk, confidence=conf, evidence_ref=ev))
        # additional items: one per remaining sentence
        for sidx, sent in enumerate(body_sentences[1:]):
            sc = f"{title}: {sent}" if title else sent
            sid = _det_hash(f"{idx}:{sidx}:{sc}")
            sl = sc.lower()
            if any(k in sl for k in high_keywords):
                conf2 = "HIGH"
            elif any(k in sl for k in low_keywords):
                conf2 = "LOW"
            else:
                conf2 = "LOW"
            risk2 = "unsafe or misleading change"
            if any(k in sl for k in ("refuse", "no-touch", "no touch", "unsafe", "no safe")):
                risk2 = "unsafe_to_act"
            ev2 = {"ptr": "/interpreted", "excerpt_hash": _det_hash(sc)}
            items.append(ChecklistItemV1(id=sid, claim=sc, obligation=sc, risk_if_false=risk2, confidence=conf2, evidence_ref=ev2))

    # ensure never empty
    if not items:
        items.append(ChecklistItemV1(id=_det_hash(text[:64]), claim=text[:200], obligation=text[:200], risk_if_false="unsafe or misleading change", confidence="LOW", evidence_ref={"ptr": "/interpreted", "excerpt_hash": _det_hash(text[:200])}))

    return items
