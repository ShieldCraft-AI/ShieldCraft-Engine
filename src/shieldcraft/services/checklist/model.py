import hashlib
from .idgen import stable_id


class ChecklistModel:
    ALLOWED_TYPES = {
        "task", "module", "fix-dependency", "resolve-invariant",
        "resolve-cycle", "integration", "bootstrap", "set-metadata"
    }
    
    # Canonical key order for to_dict()
    CANONICAL_KEYS = [
        "id", "ptr", "category", "severity", "deps", "invariants",
        "meta", "derived", "origin"
    ]
    
    def normalize_item(self, item):
        ptr = item.get("ptr")
        text = item.get("text", "")
        
        # Enforce item.id as string
        if "id" in item and not isinstance(item["id"], str):
            raise TypeError(f"Item id must be string, got {type(item['id'])}")
        
        # Enforce item.type in allowed set
        if "type" in item and item["type"] not in self.ALLOWED_TYPES:
            raise ValueError(f"Item type '{item['type']}' not in allowed set: {self.ALLOWED_TYPES}")
        
        # Enforce deterministic meta fields
        if "meta" not in item:
            item["meta"] = {}
        if not isinstance(item["meta"], dict):
            raise TypeError(f"Item meta must be dict, got {type(item['meta'])}")
        
        # Ensure unified schema fields
        if "category" not in item:
            item["category"] = self.classify(item)
        if "severity" not in item:
            item["severity"] = "medium"
        if "deps" not in item:
            item["deps"] = item.get("depends_on", [])
        if "invariants" not in item:
            item["invariants"] = item.get("invariants_from_spec", [])
        if "derived" not in item:
            item["derived"] = item.get("origin", {}).get("source") == "derived"
        if "origin" not in item:
            item["origin"] = {
                "source": "derived" if item.get("derived", False) else "spec",
                "parent": item.get("meta", {}).get("parent_id", None)
            }
        
        if "id" not in item:
            item["id"] = stable_id(ptr, text)
        return item
    
    def to_dict(self, item):
        """Convert item to dict with canonical key ordering."""
        result = {}
        for key in self.CANONICAL_KEYS:
            if key in item:
                result[key] = item[key]
        # Add remaining keys in sorted order
        for key in sorted(item.keys()):
            if key not in self.CANONICAL_KEYS:
                result[key] = item[key]
        return result

    def classify(self, item):
        ptr = item["ptr"]
        if "/metadata" in ptr:
            return "meta"
        if "/architecture" in ptr:
            return "arch"
        if "/agents" in ptr:
            return "agent"
        if "/api" in ptr:
            return "api"
        if "/governance" in ptr:
            return "gov"
        return "misc"

    def deterministic_sort(self, checklist):
        # Sort by (ptr, id) for stable order.
        return sorted(checklist, key=lambda x: (x["ptr"], x["id"]))

    def hash_id(self, ptr, text):
        # Stable ID generation helper (if needed later).
        raw = f"{ptr}:{text}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]
