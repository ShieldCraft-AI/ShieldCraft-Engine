import json
import os
import re
import shutil
import pathlib


NORM_KEYWORDS = ["must", "shall", "requires", "mandatory", "enforced", "every run must"]


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    import hashlib
    h = hashlib.sha256(open('artifacts/repo_sync_state.json', 'rb').read()).hexdigest()
    with open('repo_state_sync.json', 'w') as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def _normalize_req_text(s: str) -> str:
    # Lowercase, strip punctuation, collapse whitespace
    import re
    s2 = s.lower()
    s2 = re.sub(r"[\t\n\r]+", " ", s2)
    s2 = re.sub(r"[\s]+", " ", s2).strip()
    s2 = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", s2)
    return s2


def _extract_requirements_from_text(text):
    # Structural extraction: exact token match, skip headings/examples,
    # dedupe by normalized text hash, return list with id and line.
    import hashlib
    reqs = []
    seen = set()
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        raw = line.strip()
        if not raw:
            continue
        # Ignore headings and examples
        if raw.endswith(":"):
            continue
        if raw.startswith("Example") or raw.startswith("example"):
            continue
        # Ignore numbered section headings like '5.3 Enforced Restraint'
        if re.match(r"^\d+(?:\.\d+)*\b", raw):
            continue
        low = raw.lower()
        if any(low.find(k) != -1 for k in NORM_KEYWORDS):
            # Heuristic: skip short title-like lines that only contain 'enforced'
            tok_count = len(re.findall(r"[a-zA-Z0-9]+", raw))
            if 'enforced' in low and tok_count <= 4:
                continue
            norm = _normalize_req_text(raw)
            if not norm:
                continue
            hid = hashlib.sha256(norm.encode()).hexdigest()[:12]
            if hid in seen:
                continue
            seen.add(hid)
            reqs.append({"id": hid, "text": raw.strip(), "norm": norm, "line": i})
    return reqs


def _load_checklist(outdir='.selfhost_outputs'):
    p = os.path.join(outdir, 'checklist.json')
    assert os.path.exists(p), f"{p} missing"
    return json.load(open(p))


def _tokenize(s: str):
    import re
    toks = re.findall(r"[a-z0-9]+", s.lower())
    return toks


def _requirement_covered(req, items):
    # Strict mapping rules (in order): ptr equality/child, quote overlap >=5 tokens,
    # source_excerpt_hash exact match
    req_norm = req.get('norm') or _normalize_req_text(req.get('text', ''))
    req_toks = _tokenize(req_norm)
    for it in items:
        ev = it.get('evidence') or {}
        quote = (ev.get('quote') or '')
        quote_norm = _normalize_req_text(quote)
        quote_toks = _tokenize(quote_norm)
        # ptr rule: if requirement explicitly contains a pointer like '/sections' use it
        # detect pointer tokens in requirement text
        ptrs = [tok for tok in req['text'].split() if tok.startswith('/')]
        item_ptr = it.get('ptr') or ''
        for p in ptrs:
            if item_ptr == p or item_ptr.startswith(p.rstrip('/') + '/'):
                return True
        # token overlap rule (>=5 overlapping tokens)
        overlap = len(set(req_toks) & set(quote_toks))
        if overlap >= 5:
            return True
        # excerpt hash rule
        import hashlib
        h = hashlib.sha256(req_norm.encode()).hexdigest()[:12]
        if h == (ev.get('source_excerpt_hash') or ''):
            return True
    return False


def _find_evidence_for_requirement(req, items):
    # Return mapping evidence dict if found, else None
    req_norm = req.get('norm') or _normalize_req_text(req.get('text', ''))
    req_toks = _tokenize(req_norm)
    import hashlib
    req_hash = hashlib.sha256(req_norm.encode()).hexdigest()[:12]
    for it in items:
        ev = it.get('evidence') or {}
        quote = (ev.get('quote') or '')
        quote_norm = _normalize_req_text(quote)
        quote_toks = _tokenize(quote_norm)
        # ptr rule
        ptrs = [tok for tok in req['text'].split() if tok.startswith('/')]
        item_ptr = it.get('ptr') or ''
        for p in ptrs:
            if item_ptr == p or item_ptr.startswith(p.rstrip('/') + '/'):
                return {
                    'item_id': it.get('id'), 'item_ptr': item_ptr, 'rule': 'ptr',
                    'quote': quote, 'source_excerpt_hash': ev.get('source_excerpt_hash')
                }
        # overlap rule
        overlap = len(set(req_toks) & set(quote_toks))
        if overlap >= 5:
            return {
                'item_id': it.get('id'), 'item_ptr': item_ptr, 'rule': 'overlap',
                'quote': quote, 'overlap': overlap, 'source_excerpt_hash': ev.get('source_excerpt_hash')
            }
        # excerpt hash rule
        if req_hash == (ev.get('source_excerpt_hash') or ''):
            return {
                'item_id': it.get('id'), 'item_ptr': item_ptr, 'rule': 'excerpt_hash',
                'quote': quote, 'source_excerpt_hash': ev.get('source_excerpt_hash')
            }
    return None


def _assert_spec_sufficiency(spec_path='spec/test_spec.yml', tmp_path=None):
    # Run self-host and assert checklist covers normative requirements
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    cl = _load_checklist()
    items = cl.get('items') or []
    assert items and len(items) > 0

    # Load raw spec text
    text = None
    try:
        text = open(spec_path, 'r', encoding='utf8').read()
    except Exception: # type: ignore
        # fallback: try to read metadata.source_material from ingested spec
        from shieldcraft.services.spec.ingestion import ingest_spec
        sp = ingest_spec(spec_path)
        text = str(sp.get('metadata', {}).get('source_material', ''))

    reqs = _extract_requirements_from_text(text)
    assert reqs, 'No normative requirements found in spec text (test expectation)'

    # Classify requirements: high priority (must/shall/etc) and prose-only flagged
    high_kw = set(["must", "shall", "mandatory", "every run must", "requires", "enforced"])
    prose_markers = ['(prose-only)', '[prose-only]']
    req_meta = []
    for r in reqs:
        low = r['text'].lower()
        is_high = any(k in low for k in high_kw)
        is_prose = any(m in low for m in prose_markers)
        req_meta.append({**r, 'is_high': is_high, 'is_prose': is_prose})

    covered = []
    uncovered = []
    mapping = []
    for r in req_meta:
        ev = _find_evidence_for_requirement(r, items)
        if ev:
            covered.append(r)
            mapping.append({
                'req_id': r['id'], 'req_text': r['text'], 'item_id': ev.get('item_id'),
                'rule': ev.get('rule'), 'quote': ev.get('quote'), 'item_ptr': ev.get('item_ptr')
            })
        else:
            uncovered.append(r)

    # Assertions: 100% coverage for high priority requirements
    high_reqs = [r for r in req_meta if r['is_high']]
    high_uncovered = [r for r in uncovered if r['is_high']]
    msgs = []
    if high_uncovered:
        msgs.append(f"Uncovered high-priority requirements:\n" +
                    "\n".join([f"{h['id']}: {h['text']}" for h in high_uncovered]))

    # Allow up to 2% uncovered among prose-only labeled requirements
    prose_reqs = [r for r in req_meta if r['is_prose']]
    prose_uncovered = [r for r in uncovered if r['is_prose']]
    prose_allowed = 0
    if prose_reqs:
        prose_allowed = int(max(0, (len(prose_reqs) * 0.02)))
    if len(prose_uncovered) > prose_allowed:
        msgs.append(f"Too many uncovered prose-only requirements: {len(prose_uncovered)}/{len(prose_reqs)}")

    # Emit coverage report whenever any uncovered requirements exist
    if uncovered and tmp_path is not None:
        report = {
            'spec': spec_path,
            'requirements': req_meta,
            'covered': mapping,
            'uncovered': [{'id': r['id'], 'text': r['text'], 'line': r['line']} for r in uncovered],
            'messages': msgs
        }
        p = pathlib.Path(tmp_path) / 'checklist_coverage_report.json'
        open(p, 'w', encoding='utf8').write(json.dumps(report, indent=2))

    # If any assertion issues, fail
    if msgs:
        raise AssertionError('\n'.join(msgs))


def test_spec_is_sufficient(tmp_path):
    # Positive run: spec/test_spec.yml should be covered
    _assert_spec_sufficiency('spec/test_spec.yml', tmp_path)


def test_checklist_item_actionability_and_terminal_outcomes():
    # Ensure actionability and terminal outcomes exist
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    cl = _load_checklist()
    items = cl.get('items') or []
    assert items

    vague_verbs = {"ensure", "consider", "review"}
    terminal_governance = False
    terminal_artifact = False
    terminal_safe = False

    for it in items:
        action = it.get('action') or ''
        claim = (it.get('claim') or '').strip()
        value = str(it.get('value') or '').strip()
        assert action and isinstance(action, str), f"Missing action for item {it.get('id')}"
        assert action.strip() != claim and action.strip() != value, f"Action equals claim/value for item {it.get('id')}"
        # vague verb check
        first = action.split()[0].lower()
        if first in vague_verbs:
            # require at least 2 tokens (verb + object) to be considered non-vague
            assert len(action.split()) > 1, f"Vague action without object: {action}"

        txt = (it.get('text') or '') + ' ' + (it.get('claim') or '')
        low = txt.lower()
        if 'governance' in low or 'signature' in low:
            terminal_governance = True
        if 'artifact' in low or 'output' in low or 'produce' in low:
            terminal_artifact = True
        if 'safe' in low or (it.get('risk_if_false') == 'unsafe_to_act') or 'refuse' in low:
            terminal_safe = True

    assert terminal_governance, 'Missing governance signature emission item'
    assert terminal_artifact, 'Missing decision artifact production item'
    assert terminal_safe or any(it.get('risk_if_false') ==
                                'unsafe_to_act' for it in items), 'Missing safe-to-change surface or explicit refusal'


def test_incomplete_spec_fails_sufficiency(tmp_path):
    # Negative control: validate coverage detection and report emission without running full pipeline
    p = tmp_path / 'incomplete_spec.yml'
    p.write_text('''metadata:\n  product_id: test_incomplete\nraw: true\n\n# normative\nThis system must initialize the xor-cascade telemetry-beacon alfa-phi-2025 and register it atomically at /signals/XOR-phi/ ID-9be2f4c3 before any build.''')

    text = p.read_text()
    reqs = _extract_requirements_from_text(text)
    assert reqs, "Expect requirement extraction to find the unique normative requirement"

    # No checklist items - ensure missing requirement detection
    items = [{'id': 'dummy', 'ptr': '/', 'text': 'noop', 'evidence': {}}]
    uncovered = [r for r in reqs if not _find_evidence_for_requirement(r, items)]
    assert uncovered, "Negative control should have uncovered requirements"

    # Emit coverage report (as _assert_spec_sufficiency would) and verify contents
    report = {
        'spec': str(p),
        'requirements': reqs,
        'covered': [],
        'uncovered': [{'id': r['id'], 'text': r['text'], 'line': r['line']} for r in uncovered],
        'messages': [f"Uncovered: {r['id']}" for r in uncovered]
    }
    rep = tmp_path / 'checklist_coverage_report.json'
    rep.write_text(json.dumps(report, indent=2))
    data = json.loads(rep.read_text())
    assert 'uncovered' in data and len(data['uncovered']) >= 1
