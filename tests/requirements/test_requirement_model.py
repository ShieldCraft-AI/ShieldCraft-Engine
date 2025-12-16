import json
from shieldcraft.requirements.requirements import Requirement, from_dict
from shieldcraft.requirements.extractor import extract_requirements as extract_dicts


def test_requirements_non_empty_and_deterministic():
    txt = open('spec/test_spec.yml','r',encoding='utf8').read()
    dicts = extract_dicts(txt)
    reqs = [from_dict(d) for d in dicts]
    assert reqs and len(reqs) > 0
    # determinism check
    reqs2 = [from_dict(d) for d in extract_dicts(txt)]
    assert [r.id for r in reqs] == [r.id for r in reqs2]


def test_includes_determinism_and_refusal():
    txt = open('spec/test_spec.yml','r',encoding='utf8').read()
    dicts = extract_dicts(txt)
    texts = [d.get('text','').lower() for d in dicts]
    assert any('determin' in t for t in texts), 'No determinism requirement found'
    assert any('refus' in t or 'refuse' in t for t in texts), 'No refusal requirement found'
