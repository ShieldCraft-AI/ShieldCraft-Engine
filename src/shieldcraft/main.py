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
    parser.add_argument("--enable-persona", dest="enable_persona", action="store_true",
                        help="Enable persona influence (opt-in, auditable and non-authoritative)")
    parser.add_argument("--validate-spec", dest="validate_spec", metavar="SPEC_FILE",
                        help="Validate spec only (run preflight checks)")
    args = parser.parse_args()

    # Validate-spec mode
    if args.validate_spec:
        exit_code = validate_spec_only(args.validate_spec, args.schema)
        exit(exit_code)
    
    # Self-host mode
    if args.self_host:
        # If persona flag provided, enable via env var for Engine to pick up deterministically
        if args.enable_persona:
            os.environ["SHIELDCRAFT_PERSONA_ENABLED"] = "1"
        run_self_host(args.self_host, args.schema)
        return
    
    # Regular modes require --spec
    if not args.spec:
        parser.error("--spec is required unless using --self-host or --validate-spec")

    engine = Engine(args.schema)

    # Honor CLI persona flag in long-running modes as well
    if args.enable_persona:
        os.environ["SHIELDCRAFT_PERSONA_ENABLED"] = "1"
        engine.persona_enabled = True
    
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
    
    # Run full pipeline via the engine self-host entrypoint (centralized)
    print("[SELF-HOST] Running engine pipeline...")
    try:
        # Load spec as dict and delegate to Engine.run_self_host to ensure
        # self-host uses the single authoritative path and input/output locks.
        with open(spec_file) as sf:
            spec = json.load(sf)
        result = engine.run_self_host(spec, dry_run=False)
    except Exception as e:
        # Handle structured ValidationError specially so self-host emits a deterministic
        # `errors.json` payload that CI and tooling can consume.
        try:
            from shieldcraft.services.validator import ValidationError
        except Exception:
            ValidationError = None

        try:
            from shieldcraft.services.sync import SyncError
        except Exception:
            SyncError = None

        if ValidationError is not None and isinstance(e, ValidationError):
            print(f"[SELF-HOST] VALIDATION ERROR during execute: {e}")
            error_path = os.path.join(output_dir, "errors.json")
            with open(error_path, "w") as f:
                # serialize as a single-element `errors` list for forward compatibility
                json.dump({"errors": [e.to_dict()]}, f, indent=2, sort_keys=True)
            print(f"[SELF-HOST] Validation errors written to: {error_path}")
            return
        if SyncError is not None and isinstance(e, SyncError):
            print(f"[SELF-HOST] SYNC ERROR during execute: {e}")
            error_path = os.path.join(output_dir, "errors.json")
            with open(error_path, "w") as f:
                json.dump({"errors": [e.to_dict()]}, f, indent=2, sort_keys=True)
            print(f"[SELF-HOST] Sync errors written to: {error_path}")
            return

        try:
            from shieldcraft.snapshot import SnapshotError
        except Exception:
            SnapshotError = None

        if SnapshotError is not None and isinstance(e, SnapshotError):
            print(f"[SELF-HOST] SNAPSHOT ERROR during execute: {e}")
            error_path = os.path.join(output_dir, "errors.json")
            with open(error_path, "w") as f:
                # SnapshotError has code/message/details
                json.dump({"errors": [{"code": e.code, "message": e.message, "details": e.details}]}, f, indent=2, sort_keys=True)
            print(f"[SELF-HOST] Snapshot errors written to: {error_path}")
            return

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
        
        # Write top-level manifest and summary based on engine self-host output
        manifest_path = os.path.join(output_dir, "manifest.json")
        manifest_data = result.get("manifest", {})
        with open(manifest_path, "w") as f:
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
            summary = {
                "status": "success",
                "stable": result.get("manifest", {}).get("stable", False),
                "fingerprint": result.get("fingerprint"),
                "output_dir": result.get("output_dir"),
                "generated_files": len(result.get("outputs", [])),
                "item_count": result.get("manifest", {}).get("bootstrap_items", 0),
                "checklist_count": result.get("manifest", {}).get("bootstrap_items", 0),
                "provenance": manifest_data.get("provenance", {}),
            }
            json.dump(summary, f, indent=2, sort_keys=True)
        
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
        # CLI `validate-spec` focuses on schema, lineage and dependency checks.
        # Governance checks are advisory for this mode to allow incremental specs.
        all_ok = (
            preflight_result['schema_valid'] and
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