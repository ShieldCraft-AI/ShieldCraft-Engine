import pytest

from shieldcraft.services.checklist.extractor import SpecExtractor


def test_extractor_runs_on_minimal_spec():
    extractor = SpecExtractor()
    spec = {"metadata": {"product_id": "p"}, "sections": {}}
    res = extractor.extract(spec)
    assert isinstance(res, dict)
import json
from shieldcraft.requirements.extractor import extract_requirements
from pathlib import Path


def test_extractor_deterministic():
    p = Path('tests/fixtures/specs/litmus_full.txt')
    txt = p.read_text()
    r1 = extract_requirements(txt)
    r2 = extract_requirements(txt)
    assert r1 == r2

    # compare to golden fixture (sort by id for deterministic comparison)
    gold = json.loads(Path('tests/fixtures/requirements/litmus_full.requirements.json').read_text())
    r1s = sorted(r1, key=lambda r: r['id'])
    golds = sorted(gold, key=lambda r: r['id'])
    assert r1s == golds
