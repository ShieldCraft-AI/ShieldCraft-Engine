"""Replay engine: re-run pipeline with recorded seeds and compare outputs."""
from typing import Dict, Any
from shieldcraft.verification.determinism_contract import validate_record
from shieldcraft.verification.seed_manager import load_snapshot, snapshot, get_seed
from shieldcraft.verification.diff_explainer import explain_diff
from shieldcraft.services.governance.determinism import DeterminismEngine


def replay_and_compare(engine, record: Dict[str, Any]) -> Dict[str, Any]:
    validate_record(record)

    # Restore seeds if provided in the record; if empty, allow current engine seeds to persist
    seeds = record.get("seeds", {})
    if seeds:
        load_snapshot(engine, seeds)

    # Re-run checklist generation
    spec = record.get("spec")
    ast = record.get("ast")

    new_res = engine.checklist_gen.build(spec, ast=ast, engine=engine)

    # Compare canonicalized checklists
    de = DeterminismEngine()
    a = record.get("checklist")
    b = new_res

    # Remove embedded determinism snapshots to avoid circular references
    def _strip_det(x):
        if isinstance(x, dict):
            y = dict(x)
            y.pop("_determinism", None)
            return y
        return x

    a_clean = _strip_det(a)
    b_clean = _strip_det(b)

    if de.canonicalize(a_clean) == de.canonicalize(b_clean):
        return {"match": True}
    else:
        diff = explain_diff(a_clean, b_clean)
        # include seeds for diagnostic
        diff["seeds_used"] = snapshot(engine)
        # include seed of 'run' if available
        diff["run_seed"] = get_seed(engine, "run")
        return {"match": False, "explanation": diff}
