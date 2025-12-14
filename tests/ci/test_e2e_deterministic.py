import json
from shieldcraft.engine import Engine


def test_e2e_deterministic():
    """Full end-to-end: validate → sync → generate → self-host twice deterministically."""
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))

    # Preflight (validation + sync)
    pre = engine.preflight(spec)
    assert pre.get("ok") is True

    # Generate code (dry-run)
    code1 = engine.generate_code("spec/se_dsl_v1.spec.json", dry_run=True)

    # Self-host dry-run (mark worktree clean for test env)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)
    sh1 = engine.run_self_host(spec, dry_run=True)
    sh2 = engine.run_self_host(spec, dry_run=True)

    # Compare fingerprints and outputs
    assert sh1["fingerprint"] == sh2["fingerprint"]
    assert sh1.get("codegen_bundle_hash") == sh2.get("codegen_bundle_hash")

    outs1 = sorted(o.get("path","") for o in sh1.get("outputs", []))
    outs2 = sorted(o.get("path","") for o in sh2.get("outputs", []))
    assert outs1 == outs2

    # Verify content equality
    map1 = {o['path']: o.get('content','') for o in sh1.get('outputs',[])}
    map2 = {o['path']: o.get('content','') for o in sh2.get('outputs',[])}
    assert map1 == map2
