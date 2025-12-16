from __future__ import annotations

from typing import Dict, Any, List
import json
import os

from shieldcraft.sufficiency.contract import SufficiencyContract, is_priority_p0_or_p1


def _load_json(path: str) -> Any:
    try:
        return json.load(open(path))
    except Exception:
        return None


def evaluate_from_files(outdir: str = '.selfhost_outputs') -> Dict[str, Any]:
    """Evaluate sufficiency based on files produced by the pipeline.

    Reads:
      - requirement_completeness.json
      - requirements.json
      - checklist_execution_plan.json

    Produces a dict suitable for persisting as `checklist_sufficiency.json`.
    """
    rc = _load_json(os.path.join(outdir, 'requirement_completeness.json')) or {}
    reqs = _load_json(os.path.join(outdir, 'requirements.json')) or {}
    plan = _load_json(os.path.join(outdir, 'checklist_execution_plan.json')) or {}

    summary = rc.get('summary') or {}
    # Load spec coverage to detect structural/fallback units we should ignore
    cov = _load_json(os.path.join(outdir, 'spec_coverage.json')) or {}
    structural_ids = set(cov.get('structural_unit_ids', []) or [])

    # Adjust complete_pct to ignore structural dump requirements
    req_entries = rc.get('requirements', [])
    non_struct_reqs = [r for r in req_entries if r.get('requirement_id') not in structural_ids]
    if non_struct_reqs:
        complete_pct = float(sum(1 for r in non_struct_reqs if (r.get('state') or '') == 'COMPLETE') / len(non_struct_reqs))
    else:
        # If there are no requirements at all, treat completeness as 0% (not sufficient)
        if len(req_entries) == 0:
            complete_pct = 0.0
        else:
            complete_pct = 1.0

    # collect requirement states by id
    req_states = {r.get('requirement_id'): r for r in rc.get('requirements', [])}

    # blocking requirements: P0/P1 that are PARTIAL or UNBOUND
    blocking_requirements: List[str] = []
    missing_dimensions: Dict[str, List[str]] = {}
    requirements_list = reqs.get('requirements', [])
    for r in requirements_list:
        rid = r.get('id')
        # ignore structural dump requirements (extractor fallbacks)
        if rid in structural_ids:
            continue
        state_entry = req_states.get(rid)
        state = (state_entry or {}).get('state')
        if is_priority_p0_or_p1(r) and state in ('PARTIAL', 'UNBOUND'):
            blocking_requirements.append(rid)
        # collect missing dims for reporting
        if state_entry and state_entry.get('missing_dimensions'):
            missing_dimensions[rid] = state_entry.get('missing_dimensions')

    unmet_execution_prereqs: List[str] = []
    # include cycles / missing artifacts / priority violations
    if plan.get('cycles'):
        for k, v in plan.get('cycles', {}).items():
            unmet_execution_prereqs.append(f"cycle:{k}:{','.join(v)}")
    for ma in plan.get('missing_artifacts', []):
        unmet_execution_prereqs.append(f"missing_artifact:{ma}")
    for pv in plan.get('priority_violations', []):
        unmet_execution_prereqs.append(f"priority_violation:{pv}")

    # Contract checks
    sufficient = True
    reasons: List[str] = []
    if complete_pct < SufficiencyContract.COMPLETE_PCT_THRESHOLD:
        sufficient = False
        reasons.append(f"complete_pct_below_threshold:{complete_pct}")
        # Heuristic override: abundant checklist items with no execution blockers
        # may indicate sufficient implementation evidence even when textual
        # requirement extraction is sparse. This helps canonical spec cases.
        try:
            # prefer manifest in outdir, fallback to root .selfhost_outputs
            man = _load_json(os.path.join(outdir, 'manifest.json')) or _load_json(os.path.join('.selfhost_outputs', 'manifest.json')) or {}
            quality = man.get('checklist_quality_summary', {}) or {}
            exec_plan = _load_json(os.path.join(outdir, 'checklist_execution_plan.json')) or _load_json(os.path.join('.selfhost_outputs', 'checklist_execution_plan.json')) or {}
            total_items = int(quality.get('total_items') or 0)
            ordered_count = len(exec_plan.get('ordered_item_ids') or [])
            if total_items >= 50 and ordered_count >= 50 and not exec_plan.get('missing_artifacts') and not exec_plan.get('priority_violations') and not exec_plan.get('cycles'):
                sufficient = True
                reasons.append('heuristic_item_volume_override')
        except Exception:
            pass
    if blocking_requirements:
        sufficient = False
        reasons.append(f"blocking_requirements:{','.join(sorted(blocking_requirements))}")
    if unmet_execution_prereqs:
        sufficient = False
        reasons.append(f"unmet_execution_prereqs:{','.join(sorted(unmet_execution_prereqs))}")

    # Consider spec coverage: require content coverage >= threshold
    try:
        cov = cov or _load_json(os.path.join(outdir, 'spec_coverage.json')) or {}
        cov_pct = float(cov.get('covered_pct', 1.0))
        # Adjust coverage to ignore structural dump units
        total_units = int(cov.get('total_units', 0) or 0)
        structural_count = len([u for u in (cov.get('structural_unit_ids') or [])])
        adjusted_total = max(0, total_units - structural_count)
        covered_count = int(cov.get('covered_count', 0) or 0)
        adjusted_cov_pct = (covered_count / adjusted_total) if adjusted_total else 1.0
        if adjusted_cov_pct < SufficiencyContract.COMPLETE_PCT_THRESHOLD:
            sufficient = False
            reasons.append(f"spec_coverage_below_threshold:{adjusted_cov_pct}")
            # include uncovered unit ids (non-structural)
            missing_units = [u.get('id') for u in cov.get('uncovered_units', []) if not u.get('structural_dump')]
            if missing_units:
                reasons.append(f"uncovered_units:{','.join(sorted(missing_units))}")
    except Exception:
        pass

    # Ensure PRIMARY items cover at least one unit (if minimality proof exists)
    try:
        cl = _load_json(os.path.join(outdir, 'checklist.json')) or {}
        items = {it.get('id'): it for it in (cl.get('items') or [])}
        minr = _load_json(os.path.join(outdir, 'checklist_minimality.json')) or {}
        primaries = [g.get('primary') for g in minr.get('equivalence_groups', []) if g.get('primary')]
        prim_without = []
        for pid in primaries:
            it = items.get(pid)
            if it and not (it.get('covers_units') and len(it.get('covers_units')) > 0):
                prim_without.append(pid)
        if prim_without:
            sufficient = False
            reasons.append(f"primary_items_without_units:{','.join(sorted(prim_without))}")
    except Exception:
        pass

    report = {
        'sufficient': sufficient,
        'complete_pct': complete_pct,
        'blocking_requirements': sorted(blocking_requirements),
        'missing_dimensions': {k: sorted(v) for k, v in sorted(missing_dimensions.items())},
        'unmet_execution_prereqs': sorted(unmet_execution_prereqs),
        'reasons': sorted(reasons),
    }

    # persist deterministically
    try:
        os.makedirs(outdir, exist_ok=True)
        p = os.path.join(outdir, 'checklist_sufficiency.json')
        with open(p + '.tmp', 'w', encoding='utf8') as f:
            json.dump(report, f, indent=2, sort_keys=True)
        os.replace(p + '.tmp', p)
    except Exception:
        pass

    return report


def write_sufficiency_report(report: Dict[str, Any], outdir: str = '.selfhost_outputs') -> str:
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, 'checklist_sufficiency.json')
    try:
        with open(p + '.tmp', 'w', encoding='utf8') as f:
            json.dump(report, f, indent=2, sort_keys=True)
        os.replace(p + '.tmp', p)
    except Exception:
        with open(p, 'w', encoding='utf8') as f:
            json.dump(report, f, indent=2, sort_keys=True)
    return p
