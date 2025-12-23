import json
from shieldcraft.engine import Engine


def test_selfhost_repeatability(tmp_path):
    """Two dry-run self-host previews on the same spec must produce identical outputs."""
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec_path = "spec/se_dsl_v1.spec.json"

    r1 = engine.run_self_host(json.load(open(spec_path)), dry_run=True)
    r2 = engine.run_self_host(json.load(open(spec_path)), dry_run=True)

    # Fingerprints must match
    assert r1["fingerprint"] == r2["fingerprint"]

    # Codegen bundle hash should match
    assert r1.get("codegen_bundle_hash") == r2.get("codegen_bundle_hash")

    # Outputs list (paths) should match
    outs1 = sorted(o.get("path", "") for o in r1.get("outputs", []))
    outs2 = sorted(o.get("path", "") for o in r2.get("outputs", []))
    assert outs1 == outs2

    # And content should be identical per path
    map1 = {o['path']: o.get('content', '') for o in r1.get('outputs', [])}
    map2 = {o['path']: o.get('content', '') for o in r2.get('outputs', [])}
    assert map1 == map2
