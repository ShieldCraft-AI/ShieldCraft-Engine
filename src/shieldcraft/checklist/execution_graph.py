from __future__ import annotations

from typing import List, Dict, Any, Tuple
import json
import os

from shieldcraft.checklist.dependencies import build_graph, detect_cycles, topological_sort


def _priority_val(it: Dict[str, Any]) -> int:
    p = (it.get('priority') or '').upper()
    if p.startswith('P') and len(p) >= 2 and p[1].isdigit():
        try:
            return int(p[1])
        except Exception:
            pass
    return 5


def build_requires_map(items: List[Dict[str, Any]], inferred_deps: Dict[str, List[str]]) -> Dict[str, List[str]]:
    reqs: Dict[str, List[str]] = {}
    ids = {it.get('id') for it in items}
    for it in items:
        iid = it.get('id')
        r = []
        # explicit requires_item_ids
        r.extend(it.get('requires_item_ids') or [])
        # explicit depends_on
        r.extend(it.get('depends_on') or [])
        # inferred deps
        r.extend(inferred_deps.get(iid) or [])
        # filter to known ids and dedupe while preserving deterministic order
        seen = set()
        final = []
        for x in r:
            if x in ids and x not in seen:
                seen.add(x)
                final.append(x)
        reqs[iid] = sorted(final)
    return reqs


def detect_missing_artifact_producers(items: List[Dict[str, Any]]) -> List[str]:
    # collect produced artifacts
    produced = set()
    for it in items:
        for a in it.get('produces_artifacts') or []:
            produced.add(a)
    missing = []
    for it in items:
        for a in it.get('requires_artifacts') or []:
            if a not in produced:
                missing.append(f"{it.get('id')} requires missing_artifact:{a}")
    return missing


def check_priority_violations(items: List[Dict[str, Any]], requires_map: Dict[str, List[str]]) -> List[str]:
    id_map = {it.get('id'): it for it in items}
    violations = []
    for iid, deps in sorted(requires_map.items()):
        it = id_map.get(iid) or {}
        if it.get('priority') and it.get('priority').upper().startswith('P0'):
            for d in deps:
                dep = id_map.get(d) or {}
                if not (dep.get('priority') and dep.get('priority').upper().startswith('P0')):
                    violations.append(f"{iid} (P0) depends_on lower_priority {d}")
    return violations


def build_execution_plan(items: List[Dict[str, Any]], inferred_deps: Dict[str, List[str]], outdir: str = '.selfhost_outputs') -> Dict[str, Any]:
    requires_map = build_requires_map(items, inferred_deps)
    # build dependency graph in same shape as dependencies.build_graph (node->set(deps))
    graph = {it.get('id'): set(requires_map.get(it.get('id'), [])) for it in items}

    cycles = detect_cycles(graph)
    if cycles:
        # do not auto-resolve; surface cycles for caller to fail if needed
        cycle_groups = {f"cycle_{i}": sorted(group) for i, group in enumerate(sorted(cycles, key=lambda g: sorted(g)))}
    else:
        cycle_groups = {}

    # artifact missing check
    missing_artifacts = detect_missing_artifact_producers(items)
    priority_violations = check_priority_violations(items, requires_map)

    # compute execution order only for acyclic graph
    order = []
    execution_order = {}
    parallel_groups = []
    if not cycles:
        # topological_sort expects edges from node->children; reverse our graph
        rev_graph = {n: set() for n in graph}
        for n, deps in graph.items():
            for d in deps:
                rev_graph.setdefault(d, set()).add(n)
        order = topological_sort(rev_graph)
        for idx, nid in enumerate(order):
            execution_order[nid] = idx + 1
        # compute levels (parallel groups) by dynamic programming
        levels = {}
        for nid in order:
            deps = sorted(list(graph.get(nid, [])))
            if not deps:
                levels[nid] = 0
            else:
                levels[nid] = 1 + max(levels[d] for d in deps)
        # group by level
        max_lvl = max(levels.values()) if levels else -1
        for l in range(0, max_lvl + 1):
            group = [nid for nid, lvl in sorted(levels.items()) if lvl == l]
            if group:
                parallel_groups.append(sorted(group))

    # blocking items mapping
    blocks = {it.get('id'): sorted([n for n, deps in graph.items() if it.get('id') in deps]) for it in items}

    plan = {
        'ordered_item_ids': order,
        'parallelizable_groups': parallel_groups,
        'blocking_items': blocks,
        'cycles': cycle_groups,
        'missing_artifacts': sorted(missing_artifacts),
        'priority_violations': sorted(priority_violations)
    }

    # persist
    try:
        os.makedirs(outdir, exist_ok=True)
        p = os.path.join(outdir, 'checklist_execution_plan.json')
        with open(p + '.tmp', 'w', encoding='utf8') as f:
            json.dump(plan, f, indent=2, sort_keys=True)
        os.replace(p + '.tmp', p)
    except Exception:
        pass

    return plan
