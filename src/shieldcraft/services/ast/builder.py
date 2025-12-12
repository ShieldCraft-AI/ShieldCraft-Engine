import json
from .node import Node


class ASTBuilder:
    def __init__(self):
        self.line_map = {}  # Store source line numbers during build
        self.pointer_map = {}  # Deterministic pointer→node map
    
    @classmethod
    def from_spec(cls, spec_raw):
        """
        Build AST from raw spec dict.
        Canonical entrypoint for loader integration.
        
        Args:
            spec_raw: Raw spec dictionary
            
        Returns:
            AST root node with pointer annotations
        """
        builder = cls()
        return builder.build(spec_raw)
    
    def build(self, spec):
        """Build normalized AST with sorted keys, pointers, and parent refs."""
        root = Node("root", ptr="/")
        self._build_node(spec, root, "/")
        
        # Attach lineage_id to every node and build pointer map
        self._attach_lineage(root)
        
        return root
    
    def _attach_lineage(self, node):
        """Attach lineage_id to node and build pointer map."""
        # Compute lineage_id for this node
        node.compute_lineage_id()
        
        # Add to pointer map
        if node.ptr:
            self.pointer_map[node.ptr] = node
        
        # Recursively process children
        for child in node.children:
            self._attach_lineage(child)
    
    def get_pointer_map(self):
        """Return deterministic pointer→node map."""
        return dict(sorted(self.pointer_map.items()))
    
    def _build_node(self, obj, parent, ptr):
        """Recursively build AST with normalization."""
        if isinstance(obj, dict):
            # Convert to sorted-key dictionary
            for key in sorted(obj.keys()):
                value = obj[key]
                child_ptr = f"{ptr}/{key}" if ptr != "/" else f"/{key}"
                child = Node("dict_entry", {"key": key, "value": value}, ptr=child_ptr)
                child.parent_ptr = ptr  # Non-cyclic parent reference
                parent.add(child)
                self._build_node(value, child, child_ptr)
        
        elif isinstance(obj, list):
            # Stable array with deterministic ordering
            for idx, item in enumerate(obj):
                child_ptr = f"{ptr}/{idx}"
                child = Node("array_item", {"index": idx, "value": item}, ptr=child_ptr)
                child.parent_ptr = ptr
                parent.add(child)
                self._build_node(item, child, child_ptr)
        
        else:
            # Leaf node (scalar)
            leaf = Node("scalar", obj, ptr=ptr)
            leaf.parent_ptr = parent.ptr if hasattr(parent, 'ptr') else None
            if ptr != parent.ptr:  # Avoid duplicate
                parent.add(leaf)
    
    def collect(self, node_type, root=None, result=None):
        """Collect all nodes matching given type field."""
        if result is None:
            result = []
        
        if root is None:
            return result
        
        if root.type == node_type:
            result.append(root)
        
        for child in root.children:
            self.collect(node_type, child, result)
        
        return result

    def _walk_sections(self, sections, parent):
        for key, value in sections.items():
            node = parent.add(Node("section", value.get("description"), ptr=f"/sections/{key}"))
            self._walk_fields(value.get("fields", {}), node)

    def _walk_fields(self, fields, parent):
        for key, value in fields.items():
            parent.add(Node("field", value, ptr=f"{parent.ptr}/fields/{key}"))
