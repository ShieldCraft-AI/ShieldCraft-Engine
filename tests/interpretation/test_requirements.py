import json
from shieldcraft.interpretation.requirements import extract_requirements


def test_extract_requirements_deterministic():
    txt = open('tests/fixtures/specs/litmus_full.txt', 'r', encoding='utf8').read()
    a = extract_requirements(txt)
    b = extract_requirements(txt)
    assert a == b


def test_modality_strength_classification():
    txt = '5.3 Test Section\nThe system must enforce restraint and provide an artifact.\nThis is a narrative sentence.'
    reqs = extract_requirements(txt)
    assert len(reqs) >= 1
    musts = [r for r in reqs if r['modality'] == 'MUST']
    assert musts, 'Expected at least one MUST requirement'
    r = musts[0]
    assert r['strength'] in ('structural', 'governance', 'behavioral')
