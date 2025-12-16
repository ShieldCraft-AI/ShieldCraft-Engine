import json
import os
import shutil
import itertools
from pathlib import Path


def _minimal_for(section: str):
    mapping = {
        "sections": [{"title": "s1"}],
        "invariants": [{"id": "inv1"}],
        "instructions": [{"id": "i1", "type": "noop"}],
        "model": {"dependencies": []},
        "metadata": {"product_id": "semantic-gradient-test", "spec_format": "canonical_json_v1", "spec_version": "0.0"},
        "codegen_targets": [{"name": "default"}],
        "execution": {"steps": []},
        "pointer_map": {"map": []},
    }
    return mapping.get(section, {})


def _write_spec(base_spec, populated, path: Path):
    # base_spec is a dict; populated is iterable of section names to populate
    s = dict(base_spec)
    for sec in populated:
        s[sec] = _minimal_for(sec)
    # ensure metadata exists
    s.setdefault("metadata", {}).setdefault("product_id", "semantic-gradient-test")
    with open(path, "w") as f:
        json.dump(s, f, indent=2, sort_keys=True)


def test_semantic_gradient(tmp_path):
    from shieldcraft.main import run_self_host
    from shieldcraft.services.spec.analysis import SECTION_KEYS
    from shieldcraft.services.spec.ingestion import ingest_spec

    # Prepare baseline (the provided normalized skeleton)
    base = ingest_spec("spec/test_spec.yml")
    # Clean outputs dir if present
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'

    results = []

    # Baseline run (no additional sections populated beyond skeleton)
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    with open('.selfhost_outputs/summary.json') as f:
        s = json.load(f)
    with open('.selfhost_outputs/manifest.json') as f:
        m = json.load(f)
    baseline = {
        "populated_sections": [],
        "conversion_state": s.get("conversion_state") or m.get("conversion_state"),
        "checklist_preview_items": m.get("checklist_preview_items"),
        "state_reason": s.get("state_reason"),
        "readiness_status": s.get("readiness_status"),
    }
    results.append(baseline)

    # Single-section sweep
    sections = list(SECTION_KEYS)
    for sec in sections:
        fp = tmp_path / f"spec_one_{sec}.json"
        _write_spec(base, [sec], fp)
        run_self_host(str(fp), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        with open('.selfhost_outputs/summary.json') as f:
            s = json.load(f)
        with open('.selfhost_outputs/manifest.json') as f:
            m = json.load(f)
        results.append({
            "populated_sections": [sec],
            "conversion_state": s.get("conversion_state") or m.get("conversion_state"),
            "checklist_preview_items": m.get("checklist_preview_items"),
            "state_reason": s.get("state_reason"),
            "readiness_status": s.get("readiness_status"),
        })

    # Bounded combinations: prefer combos interacting with 'sections' or 'invariants'
    combos = []
    key_focus = ["sections", "invariants", "model", "instructions", "metadata"]
    for r in (2, 3):
        for c in itertools.combinations(key_focus, r):
            combos.append(list(c))

    # Cap total runs (including baseline + singles) to limit time
    max_runs = 50
    remaining = max_runs - len(results)
    combos = combos[:remaining]

    for combo in combos:
        fp = tmp_path / ("spec_combo_" + "_".join(combo) + ".json")
        _write_spec(base, combo, fp)
        run_self_host(str(fp), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        with open('.selfhost_outputs/summary.json') as f:
            s = json.load(f)
        with open('.selfhost_outputs/manifest.json') as f:
            m = json.load(f)
        results.append({
            "populated_sections": combo,
            "conversion_state": s.get("conversion_state") or m.get("conversion_state"),
            "checklist_preview_items": m.get("checklist_preview_items"),
            "state_reason": s.get("state_reason"),
            "readiness_status": s.get("readiness_status"),
        })

    # Persist aggregated results for inspection
    out = tmp_path / "semantic_gradient_results.json"
    out.write_text(json.dumps(results, indent=2, sort_keys=True))

    # Basic assertions: run completed and artifact exists
    assert out.exists()
    # Clean env
    os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)
