from __future__ import annotations

from typing import Dict, List, Set, Any
import json
import os


def _build_req_to_items_map(covers: List[Any]) -> Dict[str, List[str]]:
    m: Dict[str, List[str]] = {}
    for c in covers:
        m.setdefault(c.requirement_id, []).extend(c.checklist_item_ids)
    return m


def infer_item_dependencies(requirements: List[Dict[str, Any]], covers: List[Any]) -> Dict[str, List[str]]:
    """Infer per-item dependencies based on requirement-level 'depends_on' relations.

    Requirements may include a 'depends_on' list of requirement ids. For each requirement R that
    depends_on D, every checklist item covering R should depend_on all checklist items that cover D.
    """
    req_to_items = _build_req_to_items_map(covers)
    item_deps: Dict[str, List[str]] = {}
    # Build mapping of requirement id -> depends_on requirement ids
    for r in requirements:
        rid = r.get('id')
        deps = r.get('depends_on') or []
        if not deps:
            continue
        items_for_r = req_to_items.get(rid, [])
        for d in deps:
            items_for_d = req_to_items.get(d, [])
            for it in items_for_r:
                item_deps.setdefault(it, [])
                # union deps
                for dep_item in items_for_d:
                    if dep_item not in item_deps[it]:
                        item_deps[it].append(dep_item)

    return item_deps


def build_graph(items: List[Dict[str, Any]], inferred_deps: Dict[str, List[str]]) -> Dict[str, Set[str]]:
    """Return adjacency list map: node -> set(dependencies)

    Ensures every referenced id is present (missing refs are ignored here).
    """
    ids = {it.get('id') for it in items}
    g: Dict[str, Set[str]] = {i: set() for i in ids}
    # include explicit depends_on on items if present
    for it in items:
        iid = it.get('id')
        for d in (it.get('depends_on') or []) + (inferred_deps.get(iid) or []):
            if d in ids:
                g.setdefault(iid, set()).add(d)
    return g


def detect_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Tarjan-like cycle detection returning list of cycles (each as list of node ids)."""
    index = {}
    lowlink = {}
    stack = []
    onstack = set()
    cycles = []
    idx = 0

    def strongconnect(v):
        nonlocal idx
        index[v] = idx
        lowlink[v] = idx
        idx += 1
        stack.append(v)
        onstack.add(v)
        for w in graph.get(v, []):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in onstack:
                lowlink[v] = min(lowlink[v], index[w])
        if lowlink[v] == index[v]:
            # start a new SCC
            comp = []
            while True:
                w = stack.pop()
                onstack.remove(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                cycles.append(comp)

    for v in graph:
        if v not in index:
            strongconnect(v)

    return cycles


def topological_sort(graph: Dict[str, Set[str]]) -> List[str]:
    # Kahn's algorithm
    indeg = {n: 0 for n in graph}
    for n, deps in graph.items():
        for d in deps:
            indeg[d] = indeg.get(d, 0) + 0  # ensure key
    for n in graph:
        for d in graph[n]:
            indeg[d] = indeg.get(d, 0) + 1
    q = [n for n, d in sorted(indeg.items()) if d == 0]
    order = []
    while q:
        n = q.pop(0)
        order.append(n)
        for m in sorted(graph.get(n, [])):
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
    # if cycle nodes exist, they won't be in order; return partial order
    return order


def build_sequence(
    items: List[Dict[str, Any]],
    inferred_deps: Dict[str, List[str]],
    outdir: str = '.selfhost_outputs'
) -> Dict[str, Any]:
    graph = build_graph(items, inferred_deps)
    cycles = detect_cycles(graph)
    cycle_groups = {
        f"cycle_{i}": sorted(group)
        for i, group in enumerate(sorted(cycles, key=lambda g: sorted(g)))
    }

    # remove cycle edges by collapsing cycle nodes (we don't auto-resolve cycles)
    cyclic_nodes = {n for grp in cycles for n in grp}
    contracted_graph = {n: {d for d in deps if d not in cyclic_nodes}
                        for n, deps in graph.items() if n not in cyclic_nodes}

    order = topological_sort(contracted_graph)
    execution_order = {}
    for idx, nid in enumerate(order):
        execution_order[nid] = idx + 1

    # Items in cycles have no execution_order
    sequence = []
    for it in sorted(items, key=lambda x: x.get('id') or ''):
        iid = it.get('id')
        seq_entry = {
            'id': iid,
            'depends_on': sorted(list(graph.get(iid) or [])),
            'blocks': sorted([n for n, deps in graph.items() if iid in deps]),
            'execution_order': execution_order.get(iid),
            'in_cycle': None
        }
        for gid, grp in cycle_groups.items():
            if iid in grp:
                seq_entry['in_cycle'] = gid
        sequence.append(seq_entry)

    # compute longest chain (depth) on contracted_graph
    depth = {n: 1 for n in contracted_graph}
    topo = topological_sort(contracted_graph)
    for n in topo:
        for d in contracted_graph.get(n, []):
            depth[n] = max(depth[n], 1 + depth.get(d, 1))
    longest_chain = max(depth.values()) if depth else 0

    # orphan items: items with no depends_on, no blocks, and no evident requirement coverage
    orphan_count = 0
    for s in sequence:
        if not s.get('depends_on') and not s.get('blocks'):
            # heuristic: check for requirement_refs or evidence on original items
            orig = next((it for it in items if it.get('id') == s.get('id')), {})
            if not orig.get('requirement_refs') and not (
                (orig.get('evidence') or {}).get('source_excerpt_hash') or (
                    orig.get('evidence') or {}).get(
                    'source', {}).get('ptr')):
                orphan_count += 1

    # persist
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, 'checklist_sequence.json')
    with open(p, 'w', encoding='utf8') as f:
        json.dump({
            'sequence': sequence,
            'cycle_groups': cycle_groups,
            'longest_chain': longest_chain,
            'orphan_count': orphan_count
        }, f, indent=2, sort_keys=True)

    return {
        'sequence': sequence,
        'cycle_groups': cycle_groups,
        'longest_chain': longest_chain,
        'orphan_count': orphan_count}
