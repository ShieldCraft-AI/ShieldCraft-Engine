import jsonschema
import json
import pathlib


class JsonPointerException(Exception):
    pass


def resolve_pointer(pointer_str, obj):
    """Simple JSON pointer resolution."""
    if not pointer_str or pointer_str == "/":
        return obj
    
    parts = pointer_str.lstrip("/").split("/")
    current = obj
    
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                raise JsonPointerException(f"Key '{part}' not found")
            current = current[part]
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError) as e:
                raise JsonPointerException(f"Invalid array index: {part}")
        else:
            raise JsonPointerException(f"Cannot traverse into {type(current)}")
    
    return current


class SpecValidator:
    def __init__(self, schema_path="se_dsl_v1.schema.json"):
        self.schema_path = schema_path
        self.schema = None

    def load_schema(self):
        if self.schema is None:
            self.schema = json.loads(pathlib.Path(self.schema_path).read_text())

    def validate(self, spec):
        """
        Strict validation with structured error reporting.
        Validates both raw spec and normalized spec against schema.
        """
        self.load_schema()
        errors = []
        
        # Schema validation - raw spec
        try:
            jsonschema.validate(spec, self.schema)
            schema_raw_ok = True
        except jsonschema.ValidationError as e:
            schema_raw_ok = False
            errors.append({
                "pointer": "/" + "/".join(str(p) for p in e.absolute_path),
                "message": e.message,
                "stage": "raw"
            })
        
        # Normalize spec and validate again
        from shieldcraft.services.spec.schema_validator import normalize_spec
        normalized_spec = normalize_spec(spec)
        
        try:
            jsonschema.validate(normalized_spec, self.schema)
            schema_normalized_ok = True
        except jsonschema.ValidationError as e:
            schema_normalized_ok = False
            errors.append({
                "pointer": "/" + "/".join(str(p) for p in e.absolute_path),
                "message": e.message,
                "stage": "normalized"
            })
        
        # Required root fields
        required_fields = ["metadata", "model", "sections"]
        for field in required_fields:
            if field not in spec:
                errors.append({
                    "pointer": f"/{field}",
                    "message": f"Required root field '{field}' is missing"
                })
        
        # Validate JSON pointers
        errors.extend(self._validate_pointers(spec))
        
        # Validate dependencies
        errors.extend(self._validate_dependencies(spec))
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "schema_raw_ok": schema_raw_ok,
            "schema_normalized_ok": schema_normalized_ok,
            "normalized_spec": normalized_spec
        }
    
    def _validate_pointers(self, spec):
        """Validate all JSON pointers resolve to existing locations."""
        errors = []
        pointers = self._collect_pointers(spec)
        
        for ptr_str in pointers:
            try:
                resolve_pointer(ptr_str, spec)
            except JsonPointerException as e:
                errors.append({
                    "pointer": ptr_str,
                    "message": f"JSON pointer '{ptr_str}' does not resolve to a valid location: {e}"
                })
        
        return errors
    
    def _validate_dependencies(self, spec):
        """Validate all declared dependencies reference valid IDs."""
        errors = []
        
        # Collect all valid IDs
        valid_ids = set()
        self._collect_ids(spec, valid_ids)
        
        # Check all dependency references
        dep_refs = self._collect_dependency_refs(spec)
        for ref_ptr, ref_id in dep_refs:
            if ref_id not in valid_ids:
                errors.append({
                    "pointer": ref_ptr,
                    "message": f"Dependency reference '{ref_id}' does not match any declared ID"
                })
        
        return errors
    
    def _collect_pointers(self, obj, path="", result=None):
        """Recursively collect all JSON pointer references."""
        if result is None:
            result = set()
        
        if isinstance(obj, dict):
            if "ptr" in obj and isinstance(obj["ptr"], str):
                result.add(obj["ptr"])
            if "pointer" in obj and isinstance(obj["pointer"], str):
                result.add(obj["pointer"])
            for key, value in obj.items():
                self._collect_pointers(value, path + "/" + key, result)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                self._collect_pointers(item, path + "/" + str(idx), result)
        
        return result
    
    def _collect_ids(self, obj, result, path=""):
        """Recursively collect all declared IDs."""
        if isinstance(obj, dict):
            if "id" in obj and isinstance(obj["id"], str):
                result.add(obj["id"])
            for key, value in obj.items():
                self._collect_ids(value, result, path + "/" + key)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                self._collect_ids(item, result, path + "/" + str(idx))
    
    def _collect_dependency_refs(self, obj, path="", result=None):
        """Recursively collect all dependency references."""
        if result is None:
            result = []
        
        if isinstance(obj, dict):
            if "dependencies" in obj:
                deps = obj["dependencies"]
                if isinstance(deps, list):
                    for dep_id in deps:
                        if isinstance(dep_id, str):
                            result.append((path + "/dependencies", dep_id))
            if "depends_on" in obj:
                depends = obj["depends_on"]
                if isinstance(depends, list):
                    for dep_id in depends:
                        if isinstance(dep_id, str):
                            result.append((path + "/depends_on", dep_id))
            for key, value in obj.items():
                self._collect_dependency_refs(value, path + "/" + key, result)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                self._collect_dependency_refs(item, path + "/" + str(idx), result)
        
        return result
