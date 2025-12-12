"""
Dependency graph extraction and cycle detection for checklist tasks.
"""


def build_graph(items):
    """
    Build dependency graph from checklist items.
    
    Args:
        items: List of checklist items with optional 'depends_on' field
    
    Returns:
        Dict with:
        - graph: adjacency list {item_id: [dep_id1, dep_id2, ...]}
        - cycles: list of cycles detected (each cycle is a list of item_ids)
    """
    # Build adjacency list
    graph = {}
    item_ids = set()
    
    for item in items:
        item_id = item.get("id")
        if not item_id:
            continue
        
        item_ids.add(item_id)
        depends_on = item.get("depends_on", [])
        
        # Normalize depends_on to list
        if isinstance(depends_on, str):
            depends_on = [depends_on]
        elif not isinstance(depends_on, list):
            depends_on = []
        
        graph[item_id] = depends_on
    
    # Detect cycles using DFS
    cycles = []
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(node):
        """DFS with cycle detection."""
        if node in rec_stack:
            # Found a cycle - extract it from path
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return
        
        if node in visited:
            return
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        # Visit dependencies
        for dep in graph.get(node, []):
            if dep in item_ids:  # Only follow valid dependencies
                dfs(dep)
        
        path.pop()
        rec_stack.remove(node)
    
    # Run DFS from all nodes
    for item_id in sorted(item_ids):  # Sort for determinism
        if item_id not in visited:
            dfs(item_id)
    
    # Deduplicate cycles (same cycle can be found from different starting points)
    unique_cycles = []
    seen_cycle_sets = set()
    
    for cycle in cycles:
        # Normalize cycle to start from smallest ID
        if cycle:
            min_idx = cycle.index(min(cycle))
            normalized = cycle[min_idx:] + cycle[:min_idx]
            cycle_set = frozenset(normalized)
            
            if cycle_set not in seen_cycle_sets:
                seen_cycle_sets.add(cycle_set)
                unique_cycles.append(normalized)
    
    # Sort cycles for determinism
    unique_cycles.sort()
    
    return {
        "graph": graph,
        "cycles": unique_cycles
    }


def get_cycle_members(cycles):
    """
    Get set of all item IDs involved in cycles.
    
    Args:
        cycles: List of cycles from build_graph
    
    Returns:
        Set of item IDs involved in any cycle
    """
    members = set()
    for cycle in cycles:
        members.update(cycle)
    return members
