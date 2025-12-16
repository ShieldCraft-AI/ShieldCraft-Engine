from shieldcraft.util.json_canonicalizer import canonicalize
import json
import hashlib


class Node:
    def __init__(self, type, value=None, children=None, ptr=None):
        self.type = type
        self.value = value
        self.children = children or []
        self.ptr = ptr  # json pointer to original spec location
        self.parent_ptr = None  # Non-cyclic parent reference
        self.lineage_id = None  # SHA256 of pointer + type
        self.spec_id = None  # Stable spec identifier for clause-level tracing
        self.clause_type = None  # Semantic clause type (requirement/forbid/etc)

    def add(self, child):
        self.children.append(child)
        return child
    
    def to_pointer(self):
        """Return deterministic JSON pointer for this node."""
        return self.ptr if self.ptr else "/"
    
    def compute_lineage_id(self):
        """Compute lineage_id as SHA256 of pointer + type."""
        pointer = self.to_pointer()
        lineage_string = f"{pointer}:{self.type}"
        self.lineage_id = hashlib.sha256(lineage_string.encode()).hexdigest()
        # Also compute a stable spec identifier for traceability
        self.compute_spec_id()
        # Infer clause type for higher-level verification
        self.infer_clause_type()
        return self.lineage_id

    def compute_spec_id(self):
        """Compute a stable spec identifier based on pointer and node content."""
        pointer = self.to_pointer()
        base = pointer
        if isinstance(self.value, dict) and "id" in self.value:
            base = f"{pointer}:{self.value.get('id')}"
        spec_str = f"spec:{base}"
        self.spec_id = hashlib.sha256(spec_str.encode()).hexdigest()
        return self.spec_id

    def infer_clause_type(self):
        """Infer clause type from node type or explicit metadata."""
        # If explicitly provided in value, prefer that
        if isinstance(self.value, dict) and "clause_type" in self.value:
            self.clause_type = self.value.get("clause_type")
            return self.clause_type

        # Derive from node type heuristics
        t = (self.type or "").lower()
        if "require" in t or "must" in t:
            self.clause_type = "requirement"
        elif "forbid" in t or "forbid" in (str(self.value) or ""):
            self.clause_type = "forbid"
        else:
            self.clause_type = "clause"

        return self.clause_type
    
    def find(self, pointer):
        """Find node by JSON pointer."""
        if self.ptr == pointer:
            return self
        
        for child in self.children:
            result = child.find(pointer)
            if result:
                return result
        
        return None
    
    def find_all(self, key):
        """Find all nodes containing the given key in their value."""
        results = []
        
        if isinstance(self.value, dict) and key in self.value:
            results.append(self)
        
        for child in self.children:
            results.extend(child.find_all(key))
        
        return results
    
    def walk(self):
        """Generator that yields all nodes in tree order."""
        yield self
        for child in self.children:
            yield from child.walk()
    
    def to_json(self, canonical=True):
        """Convert AST to JSON representation."""
        result = {
            "type": self.type,
            "ptr": self.ptr,
            "value": self.value,
            "children": [child.to_json(canonical=False) for child in self.children]
        }
        
        if self.parent_ptr:
            result["parent_ptr"] = self.parent_ptr
        
        if canonical:
            return canonicalize(json.dumps(result))
        
        return result
    
    def deep_hash(self):
        """
        Compute SHA256 hash of canonicalized subtree.
        For deep stability checking across runs.
        
        Returns:
            str: Hex digest of subtree hash
        """
        # Build canonical representation of subtree
        canonical_repr = self._canonical_subtree()
        canonical_json = json.dumps(canonical_repr, sort_keys=True)
        
        # Compute hash
        return hashlib.sha256(canonical_json.encode()).hexdigest()
    
    def _canonical_subtree(self):
        """Build canonical representation of this node and descendants."""
        canonical = {
            "type": self.type,
            "ptr": self.ptr,
            "value": self._canonical_value(self.value),
            "children": [child._canonical_subtree() for child in sorted(
                self.children, 
                key=lambda c: c.ptr or ""
            )]
        }
        return canonical
    
    def _canonical_value(self, value):
        """Canonicalize value for hashing."""
        if isinstance(value, dict):
            return {k: self._canonical_value(v) for k, v in sorted(value.items())}
        elif isinstance(value, list):
            return [self._canonical_value(v) for v in value]
        else:
            return value

    def __repr__(self):
        return f"Node(type={self.type}, children={len(self.children)})"
