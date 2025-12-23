"""
Builds dependency graph from rules_contract.rules.
Assumes each rule may declare: depends_on: [rule_ids]
"""


def build_graph(rules):
    graph = {}
    for r in rules:
        rid = r["id"]
        deps = r.get("depends_on", [])
        graph[rid] = deps

    # Compute metadata
    total_nodes = len(graph)
    total_edges = sum(len(deps) for deps in graph.values())
    cycles = detect_cycles(graph)

    graph_metadata = {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "cycles": cycles
    }

    return graph, graph_metadata


def detect_cycles(graph):
    visited = set()
    stack = set()
    cycles = []

    def dfs(node):
        if node in stack:
            cycles.append(node)
            return
        if node in visited:
            return
        visited.add(node)
        stack.add(node)
        for nxt in graph.get(node, []):
            dfs(nxt)
        stack.remove(node)

    for n in graph:
        dfs(n)
    return cycles


def compute_hash(graph):
    """
    Compute canonical hash of dependency graph.

    Args:
        graph: dict {item_id: [dep_ids]}

    Returns:
        str: hex digest of sha256 hash
    """
    import json
    import hashlib

    # Canonicalize graph: sort keys and values
    canonical = {}
    for k in sorted(graph.keys()):
        canonical[k] = sorted(graph[k])

    # Compute hash
    canonical_json = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(canonical_json.encode()).hexdigest()
