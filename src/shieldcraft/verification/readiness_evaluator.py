"""Evaluate readiness by running a series of verification gates and recording results.

Contract notes:
- Validity vs Readiness: Validity is a structural/semantic property of the spec
    (i.e. it conforms to the DSL shape and passes the engine's semantic strictness
    checks). Readiness is an operational property describing whether the spec is
    sufficiently complete to execute or self-host (tests attached, determinism
    replay, persona checks, etc.).

    The readiness evaluator is *not* responsible for determining validity. Callers
    MUST ensure a spec has been validated prior to invoking readiness evaluation.
    As a defensive measure this evaluator accepts a `validity_passed` flag and
    will short-circuit with a stable, deterministic response when `validity_passed`
    is False.
"""
from typing import Dict, Any
from shieldcraft.services.validator.spec_gate import enforce_spec_fuzz_stability
from shieldcraft.services.validator.test_gate import enforce_tests_attached
from shieldcraft.services.validator.persona_gate import enforce_persona_veto
from shieldcraft.verification.replay_engine import replay_and_compare


def evaluate_readiness(engine, spec: Dict[str, Any], checklist_result: Dict[str,
                       Any], validity_passed: bool = True) -> Dict[str, Any]:
    """Run readiness gates and return structured pass/fail report.

    Parameters:
    - `validity_passed`: if False the evaluator short-circuits and returns a
      deterministic 'not_evaluated' readiness report. Callers should set this
      to False when the spec failed validation to avoid noisy/ambiguous
      readiness results.

    Report shape: {"ok": bool, "status": "pass"|"fail"|"not_evaluated", "results": {...}, "reason": str?}
    """

    # Short-circuit when spec validity has not been established
    if not validity_passed:
        return {"ok": False, "status": "not_evaluated", "reason": "blocked_by_invalid_spec", "results": {}}

    results: Dict[str, Any] = {}
    overall_ok = True
    blocking_count = 0
    non_blocking_count = 0

    # Gate: spec fuzz stability (non-fatal if gate unavailable)
    try:
        try:
            enforce_spec_fuzz_stability(spec, engine.checklist_gen, max_variants=3)
            gov = None
            try:
                from shieldcraft.services.governance.map import get_governance_for
                gov = get_governance_for("spec_fuzz_stability")
            except Exception:
                gov = None
            from shieldcraft.services.guidance.readiness import is_blocking
            results["spec_fuzz_stability"] = {"ok": True, "governance": gov,
                                              "blocking": is_blocking("spec_fuzz_stability")}
        except RuntimeError as e:
            gov = None
            try:
                from shieldcraft.services.governance.map import get_governance_for
                gov = get_governance_for("spec_fuzz_stability")
            except Exception:
                gov = None
            from shieldcraft.services.guidance.readiness import is_blocking
            b = is_blocking("spec_fuzz_stability")
            results["spec_fuzz_stability"] = {"ok": False, "reason": str(e), "governance": gov, "blocking": b}
            overall_ok = False
            if b:
                blocking_count += 1
            else:
                non_blocking_count += 1
    except Exception as e:
        gov = None
        try:
            from shieldcraft.services.governance.map import get_governance_for
            gov = get_governance_for("spec_fuzz_stability")
        except Exception:
            gov = None
        from shieldcraft.services.guidance.readiness import is_blocking
        b = is_blocking("spec_fuzz_stability")
        results["spec_fuzz_stability"] = {"ok": False, "reason": f"gate_error:{e}", "governance": gov, "blocking": b}
        overall_ok = False
        if b:
            blocking_count += 1
        else:
            non_blocking_count += 1

    # Gate: tests attached
    try:
        enforce_tests_attached(checklist_result.get("items", []))
        gov = None
        try:
            from shieldcraft.services.governance.map import get_governance_for
            gov = get_governance_for("tests_attached")
        except Exception:
            gov = None
        from shieldcraft.services.guidance.readiness import is_blocking
        results["tests_attached"] = {"ok": True, "governance": gov, "blocking": is_blocking("tests_attached")}
    except RuntimeError as e:
        gov = None
        try:
            from shieldcraft.services.governance.map import get_governance_for
            gov = get_governance_for("tests_attached")
        except Exception:
            gov = None
        from shieldcraft.services.guidance.readiness import is_blocking
        b = is_blocking("tests_attached")
        results["tests_attached"] = {"ok": False, "reason": str(e), "governance": gov, "blocking": b}
        overall_ok = False
        if b:
            blocking_count += 1
        else:
            non_blocking_count += 1
    except Exception as e:
        gov = None
        try:
            from shieldcraft.services.governance.map import get_governance_for
            gov = get_governance_for("tests_attached")
        except Exception:
            gov = None
        from shieldcraft.services.guidance.readiness import is_blocking
        b = is_blocking("tests_attached")
        results["tests_attached"] = {"ok": False, "reason": f"gate_error:{e}", "governance": gov, "blocking": b}
        overall_ok = False
        if b:
            blocking_count += 1
        else:
            non_blocking_count += 1

    # Gate: persona veto absence
    try:
        try:
            enforce_persona_veto(engine)
            # If no veto, enforce_persona_veto returns None; we mark ok
            gov = None
            try:
                from shieldcraft.services.governance.map import get_governance_for
                gov = get_governance_for("persona_no_veto")
            except Exception:
                gov = None
            from shieldcraft.services.guidance.readiness import is_blocking
            results["persona_no_veto"] = {"ok": True, "governance": gov, "blocking": is_blocking("persona_no_veto")}
        except RuntimeError as e:
            gov = None
            try:
                from shieldcraft.services.governance.map import get_governance_for
                gov = get_governance_for("persona_no_veto")
            except Exception:
                gov = None
            from shieldcraft.services.guidance.readiness import is_blocking
            b = is_blocking("persona_no_veto")
            results["persona_no_veto"] = {"ok": False, "reason": str(e), "governance": gov, "blocking": b}
            overall_ok = False
            if b:
                blocking_count += 1
            else:
                non_blocking_count += 1
    except Exception as e:
        gov = None
        try:
            from shieldcraft.services.governance.map import get_governance_for
            gov = get_governance_for("persona_no_veto")
        except Exception:
            gov = None
        from shieldcraft.services.guidance.readiness import is_blocking
        b = is_blocking("persona_no_veto")
        results["persona_no_veto"] = {"ok": False, "reason": f"gate_error:{e}", "governance": gov, "blocking": b}
        overall_ok = False
        if b:
            blocking_count += 1
        else:
            non_blocking_count += 1

    # Gate: determinism replay (if snapshot exists)
    try:
        det = checklist_result.get("_determinism")
        from shieldcraft.services.guidance.readiness import is_blocking
        if det:
            r = replay_and_compare(engine, det)
            if r.get("match"):
                results["determinism_replay"] = {"ok": True, "blocking": is_blocking("determinism_replay")}
            else:
                b = is_blocking("determinism_replay")
                results["determinism_replay"] = {"ok": False, "reason": r.get("explanation"), "blocking": b}
                overall_ok = False
                if b:
                    blocking_count += 1
                else:
                    non_blocking_count += 1
        else:
            # Missing determinism info is a failure
            b = is_blocking("determinism_replay")
            results["determinism_replay"] = {"ok": False, "reason": "missing_determinism_snapshot", "blocking": b}
            overall_ok = False
            if b:
                blocking_count += 1
            else:
                non_blocking_count += 1
    except Exception as e:
        b = is_blocking("determinism_replay")
        results["determinism_replay"] = {"ok": False, "reason": f"gate_error:{e}", "blocking": b}
        overall_ok = False
        if b:
            blocking_count += 1
        else:
            non_blocking_count += 1

    # Compute readiness_summary and status
    from shieldcraft.services.guidance.readiness import grade_from_counts
    grade = grade_from_counts(blocking_count, non_blocking_count)
    status = "pass" if overall_ok else "fail"
    readiness_summary = {"blocking_count": blocking_count, "non_blocking_count": non_blocking_count, "grade": grade}

    return {"ok": overall_ok, "status": status, "results": results, "readiness_summary": readiness_summary}
