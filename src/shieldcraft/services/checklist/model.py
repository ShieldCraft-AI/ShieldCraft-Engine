import hashlib
from .idgen import stable_id


class ChecklistModel:
    ALLOWED_TYPES = {
        "task", "module", "fix-dependency", "resolve-invariant",
        "resolve-cycle", "integration", "bootstrap", "set-metadata"
    }
    
    # Canonical key order for to_dict()
    CANONICAL_KEYS = [
        "id", "spec_pointer", "ptr", "test_refs", "category", "severity", "deps", "invariants",
        "meta", "derived", "origin"
    ]
    
    def normalize_item(self, item):
        # Require explicit traceability: prefer explicit 'spec_pointer'.
        if "spec_pointer" not in item and "ptr" not in item:
            # Preserve original value for auditability
            original = dict(item)
            # Record validation event and synthesize a spec_pointer instead of raising
            try:
                from shieldcraft.services.checklist.context import record_event_global
                try:
                    record_event_global("G21_CHECKLIST_MODEL_VALIDATION_ERRORS", "generation", "BLOCKER", message="missing spec pointer")
                except Exception:
                    pass
            except Exception:
                pass
            # Synthesize a fallback pointer and mark the item as invalid
            item.setdefault("ptr", "/")
            item["spec_pointer"] = item["ptr"]
            item.setdefault("meta", {})
            item["meta"].setdefault("validation_errors", []).append("missing_spec_pointer")
            # Preserve original value for provenance
            item["meta"].setdefault("original_value", original)
            # Explainability metadata for coercion
            item["meta"].setdefault("source", "coerced")
            item["meta"].setdefault("justification", "missing_spec_pointer")
            item["meta"].setdefault("justification_ptr", item.get('ptr'))
            item["meta"].setdefault("inference_type", "structural")
            item["meta"].setdefault("tier", None)
            item["severity"] = "high"
            item["quality_status"] = "INVALID"
            return item
        # Canonicalize: if spec_pointer is missing but ptr exists, set spec_pointer deterministically
        if "spec_pointer" not in item and "ptr" in item:
            item["spec_pointer"] = item["ptr"]
        # Ensure test_refs field exists (may be empty until final validation)
        # Defensive: if meta exists but is not a dict, coerce it early to avoid attribute errors
        if "meta" in item and not isinstance(item.get("meta"), dict):
            original_meta = item.get("meta")
            item["meta"] = {"coerced_meta": True}
            item["meta"].setdefault("validation_errors", []).append("item_meta_not_dict")
            item["meta"].setdefault("original_value", original_meta)
            item["meta"].setdefault("source", "coerced")
            item["meta"].setdefault("justification", "item_meta_not_dict")
            item["meta"].setdefault("inference_type", "coercion")
            item["severity"] = "high"
            item["quality_status"] = "INVALID"
        if "test_refs" not in item:
            item["test_refs"] = item.get("meta", {}).get("test_refs", [])
        ptr = item.get("ptr")
        text = item.get("text", "")
        
        # Enforce item.id as string
        if "id" in item and not isinstance(item["id"], str):
            try:
                from shieldcraft.services.checklist.context import record_event_global
                try:
                    record_event_global("G21_CHECKLIST_MODEL_VALIDATION_ERRORS", "generation", "BLOCKER", message="item id not string")
                except Exception:
                    pass
            except Exception:
                pass
            # Convert id to string and mark validation note (do not raise)
            orig_id = item.get("id")
            item["id"] = str(item.get("id"))
            item.setdefault("meta", {})
            item["meta"].setdefault("validation_errors", []).append("item_id_not_string")
            # Preserve original value for auditability
            item["meta"].setdefault("original_value", orig_id)
            # Explainability metadata for coercion
            item["meta"].setdefault("source", "coerced")
            item["meta"].setdefault("justification", "item_id_not_string")
            item["meta"].setdefault("inference_type", "coercion")
            item["severity"] = "high"
            item["quality_status"] = "INVALID"
        
        # Enforce item.type in allowed set
        if "type" in item and item["type"] not in self.ALLOWED_TYPES:
            try:
                from shieldcraft.services.checklist.context import record_event_global
                try:
                    record_event_global("G21_CHECKLIST_MODEL_VALIDATION_ERRORS", "generation", "BLOCKER", message="item type not allowed", evidence={"type": item.get('type')})
                except Exception:
                    pass
            except Exception:
                pass
            # Replace invalid type with 'task' fallback and mark invalid (do not raise)
            original_type = item.get('type')
            item.setdefault("meta", {})
            item["meta"].setdefault("validation_errors", []).append(f"item_type_not_allowed:{item.get('type')}")
            # Preserve original value for auditability
            item["meta"].setdefault("original_value", original_type)
            # Explainability metadata for coercion/fallback
            item["meta"].setdefault("source", "coerced")
            item["meta"].setdefault("justification", f"item_type_not_allowed:{original_type}")
            item["meta"].setdefault("inference_type", "coercion")
            item["severity"] = "high"
            item["quality_status"] = "INVALID"
            item["type"] = "task"
        
        # Enforce deterministic meta fields
        if "meta" not in item:
            item["meta"] = {}
        if not isinstance(item["meta"], dict):
            try:
                from shieldcraft.services.checklist.context import record_event_global
                try:
                    record_event_global("G21_CHECKLIST_MODEL_VALIDATION_ERRORS", "generation", "BLOCKER", message="item meta not dict")
                except Exception:
                    pass
            except Exception:
                pass
            # Preserve original meta object for auditability
            original_meta = item.get('meta')
            # Coerce meta to dict and mark validation error (do not raise)
            item["meta"] = {"coerced_meta": True}
            item["meta"].setdefault("validation_errors", []).append("item_meta_not_dict")
            # Preserve original value for lineage
            item["meta"].setdefault("original_value", original_meta)
            # Explainability metadata for coercion
            item["meta"].setdefault("source", "coerced")
            item["meta"].setdefault("justification", "item_meta_not_dict")
            item["meta"].setdefault("inference_type", "coercion")
            item["severity"] = "high"
            item["quality_status"] = "INVALID"
        
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
