"""Spec gating utilities to enforce fuzz stability before generation."""
from shieldcraft.verification.spec_fuzzer import generate_mutations, classify_mutation
from shieldcraft.verification.failure_classes import SPEC_CONTRADICTORY, SPEC_INCOMPLETE


def enforce_spec_fuzz_stability(spec: dict, generator, max_variants: int = 5) -> None:
    """Run spec mutations and ensure checklist shape is stable and no critical failures.

    Raises RuntimeError on detected classified failures or checklist drift.
    """
    # Build baseline checklist (dry run to avoid artifact emission)
    baseline = generator.build(spec, dry_run=True, run_fuzz=False, run_test_gate=False)
    base_items = baseline.get("items") or baseline.get("checklist", {}).get("items", []) or []
    base_shape = {it.get("ptr") for it in base_items}

    muts = generate_mutations(spec)
    for mutated_spec, kind, desc in muts[:max_variants]:
        cls = classify_mutation(spec, mutated_spec, kind)
        if cls in (SPEC_CONTRADICTORY, SPEC_INCOMPLETE):
            raise RuntimeError(f"{cls}:{desc}")

        # For stable classification, ensure checklist shape unchanged (disable nested fuzzing)
        mutated_res = generator.build(mutated_spec, dry_run=True, run_fuzz=False, run_test_gate=False)
        mut_items = mutated_res.get("items") or mutated_res.get("checklist", {}).get("items", []) or []
        mut_shape = {it.get("ptr") for it in mut_items}
        if base_shape != mut_shape:
            raise RuntimeError(f"SPEC_DRIFT:{kind}:{desc}")
