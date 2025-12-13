import argparse
import json
import pathlib
import os
import shutil
from shieldcraft.engine import Engine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=False)
    parser.add_argument("--schema", default="src/shieldcraft/dsl/schema/se_dsl.schema.json")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--evidence", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--self-host", dest="self_host", metavar="PRODUCT_SPEC_FILE",
                        help="Run self-host dry-run pipeline")
    parser.add_argument("--validate-spec", dest="validate_spec", metavar="SPEC_FILE",
                        help="Validate spec only (run preflight checks)")
    args = parser.parse_args()

    # Validate-spec mode
    if args.validate_spec:
        exit_code = validate_spec_only(args.validate_spec, args.schema)
        exit(exit_code)
    
    # Self-host mode
    if args.self_host:
        run_self_host(args.self_host, args.schema)
        return
    
    # Regular modes require --spec
    if not args.spec:
        parser.error("--spec is required unless using --self-host or --validate-spec")

    engine = Engine(args.schema)
    
    if args.all:
        out = engine.execute(args.spec)
        print(json.dumps(out, indent=2))
        return
    
    if args.evidence:
        result = engine.run(args.spec)
        bundle = engine.generate_evidence(args.spec, result["checklist"])
        print(json.dumps(bundle, indent=2))
        return
    
    if args.generate:
        r = engine.generate_code(args.spec)
        print(json.dumps(r, indent=2))
        return
    
    result = engine.run(args.spec)
    print(json.dumps(result, indent=2))


def run_self_host(spec_file, schema_path):
    """
    Run self-host dry-run pipeline.
    Steps:
    1. Load spec
    2. Run full engine pipeline
    3. Write outputs to .selfhost_outputs/
    No side effects outside that directory.
    """
    output_dir = ".selfhost_outputs"
    
    # Clean output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"[SELF-HOST] Starting self-host pipeline for: {spec_file}")
    print(f"[SELF-HOST] Output directory: {output_dir}")
    
    # Load spec
    print("[SELF-HOST] Loading spec...")
    engine = Engine(schema_path)
    
    # Run full pipeline
    print("[SELF-HOST] Running engine pipeline...")
    try:
        result = engine.execute(spec_file)
    except Exception as e:
        print(f"[SELF-HOST] ERROR during execute: {e}")
        import traceback
        error_path = os.path.join(output_dir, "error.txt")
        with open(error_path, "w") as f:
            f.write(str(e))
            f.write("\n\n")
            f.write(traceback.format_exc())
        print(f"[SELF-HOST] Error details: {error_path}")
        return
    
    try:
        if result.get("type") == "schema_error":
            print("[SELF-HOST] ERROR: Schema validation failed")
            error_path = os.path.join(output_dir, "errors.json")
            with open(error_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"[SELF-HOST] Errors written to: {error_path}")
            return
        
        # Write outputs
        print("[SELF-HOST] Writing outputs...")
        
        # Write manifest
        manifest_path = os.path.join(output_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            checklist_data = result.get("checklist", {})
            # Handle both dict and list responses
            if isinstance(checklist_data, dict):
                checklist_items = checklist_data.get("items", [])
            else:
                checklist_items = []
            
            # Compute a lightweight fingerprint for deterministic identification
            try:
                from shieldcraft.services.spec.fingerprint import compute_spec_fingerprint
                spec_fp = compute_spec_fingerprint(result.get("spec", {}))
            except Exception:
                spec_fp = "unknown"

            manifest_data = {
                "manifest_version": "v1",
                "spec_fingerprint": spec_fp,
                "checklist": checklist_data,
                "plan": result.get("plan", {}),
                "lineage": result.get("lineage", {})
            }
            json.dump(manifest_data, f, indent=2, sort_keys=True)
        
        # Write generated code
        if "generated" in result:
            code_dir = os.path.join(output_dir, "generated")
            os.makedirs(code_dir, exist_ok=True)
            for idx, output in enumerate(result["generated"]):
                code_path = os.path.join(code_dir, f"output_{idx}.py")
                with open(code_path, "w") as f:
                    f.write(output.get("content", ""))
        
        # Write summary
        summary_path = os.path.join(output_dir, "summary.json")
        with open(summary_path, "w") as f:
            checklist_data = result.get("checklist", {})
            if isinstance(checklist_data, dict):
                item_count = len(checklist_data.get("items", []))
            else:
                item_count = 0
            
            summary = {
                "status": "success",
                "stable": result.get("stable", False),
                "item_count": item_count,
                "generated_files": len(result.get("generated", []))
            }
            json.dump(summary, f, indent=2)
        
        print(f"[SELF-HOST] SUCCESS")
        print(f"[SELF-HOST] Manifest: {manifest_path}")
        print(f"[SELF-HOST] Summary: {summary_path}")
        
    except Exception as e:
        print(f"[SELF-HOST] ERROR: {e}")
        import traceback
        error_path = os.path.join(output_dir, "error.txt")
        with open(error_path, "w") as f:
            f.write(str(e))
            f.write("\n\n")
            f.write(traceback.format_exc())
        print(f"[SELF-HOST] Error details: {error_path}")

def validate_spec_only(spec_file, schema_path):
    """
    Validate spec file only - run preflight checks.
    Returns: exit code (0 = success, 1 = failure)
    """
    print(f"[VALIDATE] Validating spec: {spec_file}")
    
    try:
        # Load spec
        with open(spec_file) as f:
            spec = json.load(f)
        
        # Load schema
        with open(schema_path) as f:
            schema = json.load(f)
        
        # Run preflight
        from shieldcraft.services.preflight.preflight import run_preflight
        preflight_result = run_preflight(spec, schema, [])
        
        # Print summary
        print("\n[VALIDATE] Preflight Results:")
        print(f"  Schema Valid: {preflight_result['schema_valid']}")
        print(f"  Governance OK: {preflight_result['governance_ok']}")
        print(f"  Lineage OK: {preflight_result['lineage_ok']}")
        print(f"  Dependency OK: {preflight_result.get('dependency_ok', True)}")
        
        if preflight_result.get("schema_errors"):
            print(f"\n  Schema Errors: {len(preflight_result['schema_errors'])}")
            for err in preflight_result['schema_errors'][:5]:  # Show first 5
                print(f"    - {err}")
        
        if preflight_result.get("governance_violations"):
            print(f"\n  Governance Violations: {len(preflight_result['governance_violations'])}")
            for violation in preflight_result['governance_violations'][:5]:
                print(f"    - {violation}")
        
        if preflight_result.get("unresolved_dependencies"):
            print(f"\n  Unresolved Dependencies: {len(preflight_result['unresolved_dependencies'])}")
            for dep in preflight_result['unresolved_dependencies'][:5]:
                print(f"    - {dep}")
        
        # Determine overall status
        all_ok = (
            preflight_result['schema_valid'] and
            preflight_result['governance_ok'] and
            preflight_result['lineage_ok'] and
            preflight_result.get('dependency_ok', True)
        )
        
        if all_ok:
            print("\n[VALIDATE] ✓ Spec is valid")
            return 0
        else:
            print("\n[VALIDATE] ✗ Spec validation failed")
            return 1
    
    except FileNotFoundError as e:
        print(f"[VALIDATE] ERROR: File not found - {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"[VALIDATE] ERROR: Invalid JSON - {e}")
        return 1
    except Exception as e:
        print(f"[VALIDATE] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()