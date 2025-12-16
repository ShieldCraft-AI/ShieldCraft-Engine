import json
from shieldcraft.engine import Engine


def test_codegen_regeneration_equivalence():
    """Two dry-run self-host previews on the same spec must produce identical codegen bundle hashes and outputs."""
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))

    r1 = engine.run_self_host(spec, dry_run=True)
    r2 = engine.run_self_host(spec, dry_run=True)

    assert r1.get("codegen_bundle_hash") == r2.get("codegen_bundle_hash")

    outs1 = sorted(o.get("path", "") for o in r1.get("outputs", []))
    outs2 = sorted(o.get("path", "") for o in r2.get("outputs", []))
    assert outs1 == outs2

    map1 = {o['path']: o.get('content','') for o in r1.get('outputs',[])}
    map2 = {o['path']: o.get('content','') for o in r2.get('outputs',[])}
    assert map1 == map2
