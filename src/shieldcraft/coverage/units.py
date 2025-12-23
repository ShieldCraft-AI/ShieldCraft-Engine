from __future__ import annotations

from typing import List, Dict, Any
import hashlib
import json

from shieldcraft.requirements.extractor import extract_requirements


def _stable_id(ptr: str, text: str) -> str:
    h = hashlib.sha256((ptr + ':' + (text or '')).encode()).hexdigest()[:12]
    return h


def build_units_from_spec(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Construct coverage units from spec structure.

    Units produced:
      - sections (top-level 'sections' entries)
      - numbered requirements (canonical extractor)
      - invariants/constraints entries
      - artifact contract / outputs if present
    """
    units: List[Dict[str, Any]] = []

    # sections
    sections = spec.get('sections') or {}
    if isinstance(sections, dict):
        for k in sorted(sections.keys()):
            ptr = f"/sections/{k}"
            text = str(sections.get(k) or '')
            units.append({'id': _stable_id(ptr, text), 'ptr': ptr, 'text': text, 'kind': 'section'})
    elif isinstance(sections, list):
        for i, v in enumerate(sections):
            ptr = f"/sections/{i}"
            text = str(v or '')
            units.append({'id': _stable_id(ptr, text), 'ptr': ptr, 'text': text, 'kind': 'section'})

    # numbered / normative requirements via extractor
    try:
        # extractor expects raw text
        raw = spec.get('metadata', {}).get('source_material') or json.dumps(spec, sort_keys=True)
        reqs = extract_requirements(raw)
        for r in sorted(reqs, key=lambda x: x.get('id')):
            ptr = f"/requirements/{r.get('id')}"
            text = r.get('text')
            # Detect extractor fallbacks that emit raw JSON dumps as requirement text
            structural = isinstance(text, str) and text.strip().startswith('{')
            u = {'id': r.get('id'), 'ptr': ptr, 'text': text, 'kind': 'requirement'}
            if structural:
                u['structural_dump'] = True
            units.append(u)
    except (AttributeError, TypeError):
        pass

    # invariants / constraints
    inv = spec.get('invariants') or []
    if isinstance(inv, list):
        for i, v in enumerate(inv):
            ptr = f"/invariants/{i}"
            text = str(v or '')
            units.append({'id': _stable_id(ptr, text), 'ptr': ptr, 'text': text, 'kind': 'invariant'})

    # artifact contract / outputs
    ac = spec.get('metadata', {}).get('artifact_contract') or spec.get('outputs') or []
    if isinstance(ac, dict):
        for k, v in sorted(ac.items()):
            ptr = f"/artifact_contract/{k}"
            text = str(v or '')
            units.append({'id': _stable_id(ptr, text), 'ptr': ptr, 'text': text, 'kind': 'artifact'})
    elif isinstance(ac, list):
        for i, v in enumerate(ac):
            ptr = f"/artifact_contract/{i}"
            text = str(v or '')
            units.append({'id': _stable_id(ptr, text), 'ptr': ptr, 'text': text, 'kind': 'artifact'})

    # Deduplicate by id deterministically
    seen = set()
    res = []
    for u in sorted(units, key=lambda x: (x.get('kind') or '', x.get('ptr') or '', x.get('id'))):
        if u['id'] in seen:
            continue
        seen.add(u['id'])
        res.append(u)
    return res
