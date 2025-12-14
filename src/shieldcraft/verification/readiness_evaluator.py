"""Evaluate readiness by running a series of verification gates and recording results."""
from typing import Dict, Any
from shieldcraft.verification.readiness_contract import REQUIRED_GATES
from shieldcraft.services.validator.spec_gate import enforce_spec_fuzz_stability
from shieldcraft.services.validator.test_gate import enforce_tests_attached
from shieldcraft.services.validator.persona_gate import enforce_persona_veto
from shieldcraft.verification.replay_engine import replay_and_compare


def evaluate_readiness(engine, spec: Dict[str, Any], checklist_result: Dict[str, Any]) -> Dict[str, Any]:
    """Run readiness gates and return structured pass/fail report.

    Report shape: {"ok": bool, "results": {gate: {"ok": bool, "reason": str}}}
    """
    results: Dict[str, Any] = {}
    overall_ok = True

    # Gate: spec fuzz stability (non-fatal if gate unavailable)
    try:
        try:
            enforce_spec_fuzz_stability(spec, engine.checklist_gen, max_variants=3)
            results["spec_fuzz_stability"] = {"ok": True}
        except RuntimeError as e:
            results["spec_fuzz_stability"] = {"ok": False, "reason": str(e)}
            overall_ok = False
    except Exception as e:
        results["spec_fuzz_stability"] = {"ok": False, "reason": f"gate_error:{e}"}
        overall_ok = False

    # Gate: tests attached
    try:
        enforce_tests_attached(checklist_result.get("items", []))
        results["tests_attached"] = {"ok": True}
    except RuntimeError as e:
        results["tests_attached"] = {"ok": False, "reason": str(e)}
        overall_ok = False
    except Exception as e:
        results["tests_attached"] = {"ok": False, "reason": f"gate_error:{e}"}
        overall_ok = False

    # Gate: persona veto absence
    try:
        try:
            enforce_persona_veto(engine)
            # If no veto, enforce_persona_veto returns None; we mark ok
            results["persona_no_veto"] = {"ok": True}
        except RuntimeError as e:
            results["persona_no_veto"] = {"ok": False, "reason": str(e)}
            overall_ok = False
    except Exception as e:
        results["persona_no_veto"] = {"ok": False, "reason": f"gate_error:{e}"}
        overall_ok = False

    # Gate: determinism replay (if snapshot exists)
    try:
        det = checklist_result.get("_determinism")
        if det:
            r = replay_and_compare(engine, det)
            if r.get("match"):
                results["determinism_replay"] = {"ok": True}
            else:
                results["determinism_replay"] = {"ok": False, "reason": r.get("explanation")}
                overall_ok = False
        else:
            # Missing determinism info is a failure
            results["determinism_replay"] = {"ok": False, "reason": "missing_determinism_snapshot"}
            overall_ok = False
    except Exception as e:
        results["determinism_replay"] = {"ok": False, "reason": f"gate_error:{e}"}
        overall_ok = False

    return {"ok": overall_ok, "results": results}
