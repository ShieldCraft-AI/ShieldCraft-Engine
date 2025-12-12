#!/usr/bin/env python3
"""
Emit manifest in dry-run mode for CI validation.
"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shieldcraft.dsl.loader import load_spec
from shieldcraft.services.spec.schema_validator import validate_spec_against_schema
from shieldcraft.services.io.manifest_writer import write_manifest_v2


def main():
    spec_path = "spec/se_dsl_v1.spec.json"
    schema_path = "spec/schemas/se_dsl_v1.schema.json"
    
    # Load spec using canonical DSL
    spec = load_spec(spec_path)
    
    # Extract raw dict from SpecModel if needed
    if hasattr(spec, 'raw'):
        spec_raw = spec.raw
    else:
        spec_raw = spec
    
    # Validate
    valid, errors = validate_spec_against_schema(spec_raw, schema_path)
    
    if not valid:
        print("ERROR: Schema validation failed")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Create dry-run manifest preview
    manifest_data = {
        "spec_path": spec_path,
        "product_id": spec_raw.get("metadata", {}).get("product_id", "unknown"),
        "version": spec_raw.get("metadata", {}).get("version", "unknown"),
        "validation": "passed",
        "dry_run": True
    }
    
    # Write preview
    Path("artifacts").mkdir(exist_ok=True)
    with open("artifacts/manifest_preview.json", "w") as f:
        json.dump(manifest_data, f, indent=2)
    
    print("Manifest preview written to artifacts/manifest_preview.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
