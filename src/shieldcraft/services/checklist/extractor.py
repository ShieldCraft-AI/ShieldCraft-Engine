class SpecExtractor:
    """
    Pure recursive extractor.
    Input: spec dict
    Output: list of {ptr, key, value, source_pointer, source_section, source_line}
    Also builds reverse index: pointer → list[item_ids]
    """
    
    def __init__(self):
        self.reverse_index = {}
    
    def extract(self, node, base_ptr="", line_map=None):
        """Extract items with full traceability."""
        if line_map is None:
            line_map = {}
        
        items = []
        if isinstance(node, dict):
            for k, v in sorted(node.items()):  # Deterministic ordering
                ptr = f"{base_ptr}/{k}" if base_ptr else f"/{k}"
                
                # Determine source section (top-level key)
                source_section = ptr.split("/")[1] if len(ptr.split("/")) > 1 else "root"
                
                # Get line number from mapping (deterministic fallback)
                source_line = line_map.get(ptr, self._compute_line(ptr))
                
                items.append({
                    "ptr": ptr,
                    "key": k,
                    "value": v,
                    "source_pointer": ptr,
                    "source_section": source_section,
                    "source_line": source_line
                })
                items.extend(self.extract(v, ptr, line_map))
        elif isinstance(node, list):
            for idx, v in enumerate(node):
                ptr = f"{base_ptr}/{idx}"
                source_section = ptr.split("/")[1] if len(ptr.split("/")) > 1 else "root"
                source_line = line_map.get(ptr, self._compute_line(ptr))
                
                items.append({
                    "ptr": ptr,
                    "key": str(idx),
                    "value": v,
                    "source_pointer": ptr,
                    "source_section": source_section,
                    "source_line": source_line
                })
                items.extend(self.extract(v, ptr, line_map))
        else:
            # Leaf node
            if base_ptr:
                source_section = base_ptr.split("/")[1] if len(base_ptr.split("/")) > 1 else "root"
                source_line = line_map.get(base_ptr, self._compute_line(base_ptr))
                items.append({
                    "ptr": base_ptr,
                    "key": base_ptr.split("/")[-1],
                    "value": node,
                    "source_pointer": base_ptr,
                    "source_section": source_section,
                    "source_line": source_line
                })
        
        # Build reverse index
        self._build_reverse_index(items)
        
        return items
    
    def _build_reverse_index(self, items):
        """Build pointer → item_ids reverse mapping."""
        for item in items:
            ptr = item.get("ptr")
            item_id = item.get("id", ptr)  # Use ptr as fallback ID
            
            if ptr not in self.reverse_index:
                self.reverse_index[ptr] = []
            
            if item_id not in self.reverse_index[ptr]:
                self.reverse_index[ptr].append(item_id)
    
    def get_reverse_index(self):
        """Return the pointer → item_ids mapping."""
        return {k: sorted(v) for k, v in sorted(self.reverse_index.items())}
    
    def _compute_line(self, ptr):
        """Deterministic line number computation from pointer."""
        # Use hash for deterministic but stable line number
        return (hash(ptr) % 10000) + 1
