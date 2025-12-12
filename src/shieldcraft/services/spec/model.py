"""
Internal spec model for SE.
Encapsulates raw spec, AST, and fingerprint.
"""


class SpecModel:
    """
    Internal representation of a spec with computed artifacts.
    """
    
    def __init__(self, raw, ast, fingerprint, strict_mode=False):
        self.raw = raw
        self.ast = ast
        self.fingerprint = fingerprint
        self.strict_mode = strict_mode
    
    def get_sections(self):
        """Return list of section keys from raw spec."""
        sections = self.raw.get("sections", [])
        if isinstance(sections, dict):
            return sorted(sections.keys())
        elif isinstance(sections, list):
            # For array-based sections, return list of section ids
            return [sec.get("id", f"section_{i}") for i, sec in enumerate(sections)]
        return []
    
    def get_dependencies(self):
        """
        Extract dependency references from raw spec.
        Deterministic extraction and sorting.
        """
        deps = []
        sections = self.raw.get("sections", {})
        
        for section_key in sorted(sections.keys()):
            section = sections[section_key]
            if isinstance(section, dict):
                # Look for dependency fields
                if "dependencies" in section:
                    dep_list = section["dependencies"]
                    if isinstance(dep_list, list):
                        for dep in dep_list:
                            if isinstance(dep, str):
                                deps.append({
                                    "source": section_key,
                                    "target": dep,
                                    "type": "direct"
                                })
                            elif isinstance(dep, dict):
                                deps.append({
                                    "source": section_key,
                                    "target": dep.get("id", ""),
                                    "type": dep.get("type", "direct")
                                })
                
                # Recursively check nested structures
                self._extract_deps_recursive(section, section_key, deps)
        
        # Deduplicate and sort
        unique_deps = []
        seen = set()
        for dep in sorted(deps, key=lambda d: (d["source"], d["target"], d["type"])):
            key = (dep["source"], dep["target"], dep["type"])
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)
        
        return unique_deps
    
    def _extract_deps_recursive(self, obj, context, deps):
        """Recursively extract dependencies from nested structures."""
        if isinstance(obj, dict):
            for key in sorted(obj.keys()):
                if key == "depends_on" or key == "requires":
                    dep_ref = obj[key]
                    if isinstance(dep_ref, str):
                        deps.append({
                            "source": context,
                            "target": dep_ref,
                            "type": "reference"
                        })
                    elif isinstance(dep_ref, list):
                        for ref in dep_ref:
                            if isinstance(ref, str):
                                deps.append({
                                    "source": context,
                                    "target": ref,
                                    "type": "reference"
                                })
                elif isinstance(obj[key], (dict, list)):
                    self._extract_deps_recursive(obj[key], context, deps)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    self._extract_deps_recursive(item, context, deps)
    
    def get_all_pointers(self):
        """
        Return all JSON pointers found in raw spec.
        Deterministic ordering.
        """
        pointers = set()
        
        def walk(obj, path=""):
            if isinstance(obj, dict):
                for key in sorted(obj.keys()):
                    new_path = f"{path}/{key}"
                    pointers.add(new_path)
                    walk(obj[key], new_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    new_path = f"{path}/{idx}"
                    pointers.add(new_path)
                    walk(item, new_path)
        
        walk(self.raw)
        return sorted(pointers)
    
    def get_invariants(self):
        """
        Extract invariants from AST.
        Returns structured invariant objects with canonical sorting.
        """
        from shieldcraft.services.checklist.invariants import extract_invariants
        return extract_invariants(self.ast)
    
    def get_entity_map(self):
        """
        Map top-level nodes to AST node IDs.
        Returns deterministic mapping of entity paths to AST node identifiers.
        """
        entity_map = {}
        
        # Walk AST and map top-level entities
        for node in self.ast.walk():
            if node.ptr and node.ptr.count('/') == 2:  # Top-level: /section/entity
                entity_map[node.ptr] = {
                    "node_id": id(node),
                    "type": node.type,
                    "ptr": node.ptr
                }
        
        # Return sorted by pointer for determinism
        return dict(sorted(entity_map.items()))
    
    def validate_pointer_strict_mode(self, checklist_items):
        """
        Validate that all spec pointers are covered by checklist items.
        Only enforced when strict_mode is True.
        
        Returns: (ok: bool, missing_pointers: list)
        """
        if not self.strict_mode:
            return True, []
        
        all_pointers = set(self.get_all_pointers())
        covered_pointers = set()
        
        # Extract pointers from checklist items
        for item in checklist_items:
            ptr = item.get("ptr", "")
            if ptr:
                covered_pointers.add(ptr)
                # Also cover parent paths
                parts = ptr.split("/")
                for i in range(1, len(parts)):
                    parent_path = "/".join(parts[:i])
                    if parent_path:
                        covered_pointers.add(parent_path)
        
        missing = all_pointers - covered_pointers
        
        return len(missing) == 0, sorted(missing)
    
    def get_pointer_map(self):
        """
        Return mapping of pointer → value from raw spec.
        Deterministic ordering.
        """
        pointer_map = {}
        
        def walk(obj, path=""):
            if isinstance(obj, dict):
                for key in sorted(obj.keys()):
                    new_path = f"{path}/{key}"
                    pointer_map[new_path] = obj[key]
                    walk(obj[key], new_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    new_path = f"{path}/{idx}"
                    pointer_map[new_path] = item
                    walk(item, new_path)
        
        walk(self.raw)
        return dict(sorted(pointer_map.items()))
    
    def get_all_lineage_ids(self):
        """
        Return set of all lineage IDs from AST.
        """
        lineage_ids = set()
        
        for node in self.ast.walk():
            if node.lineage_id:
                lineage_ids.add(node.lineage_id)
        
        return lineage_ids
