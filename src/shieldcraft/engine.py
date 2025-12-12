import json
import os
from shieldcraft.util.json_canonicalizer import canonicalize
from shieldcraft.dsl.loader import DSLLoader
from shieldcraft.services.ast.builder import ASTBuilder
from shieldcraft.services.planner.planner import Planner
from shieldcraft.services.checklist.generator import ChecklistGenerator
from shieldcraft.services.codegen.generator import CodeGenerator
from shieldcraft.services.codegen.emitter.writer import FileWriter
from shieldcraft.services.governance.determinism import DeterminismEngine
from shieldcraft.services.governance.provenance import ProvenanceEngine
from shieldcraft.services.governance.evidence import EvidenceBundle
from shieldcraft.services.governance.verifier import ChecklistVerifier
from shieldcraft.services.dsl.loader import SpecLoader
from shieldcraft.services.dsl.validator import SpecValidator
from shieldcraft.services.plan.execution_plan import from_ast
from shieldcraft.services.io.canonical_writer import write_canonical_json
from shieldcraft.services.artifacts.lineage import bundle
from shieldcraft.services.io.manifest_writer import write_manifest_v2
from shieldcraft.services.diff.impact import impact_summary
from shieldcraft.services.stability.stability import compare


class Engine:
    def __init__(self, schema_path):
        self.dsl_loader = DSLLoader(schema_path)
        self.loader = SpecLoader()
        self.validator = SpecValidator(schema_path)
        self.ast = ASTBuilder()
        self.planner = Planner()
        self.checklist_gen = ChecklistGenerator()
        self.codegen = CodeGenerator()
        self.writer = FileWriter()
        self.det = DeterminismEngine()
        self.prov = ProvenanceEngine()
        self.evidence = EvidenceBundle(self.det, self.prov)
        self.verifier = ChecklistVerifier()

    def run(self, spec_path):
        # Load spec
        spec = self.loader.load(spec_path)
        
        # DSL validation with structured errors
        validation_result = self.validator.validate(spec)
        if not validation_result["valid"]:
            return {"type": "schema_error", "details": validation_result["errors"]}
        
        # Build AST
        ast = self.ast.build(spec)
        
        # Create execution plan
        plan = from_ast(ast)
        
        # Store plan context
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        plan_dir = f"products/{product_id}"
        os.makedirs(plan_dir, exist_ok=True)
        write_canonical_json(f"{plan_dir}/plan.json", plan)
        
        # Generate checklist using AST
        checklist = self.checklist_gen.build(spec, ast=ast)
        
        return {"spec": spec, "ast": ast, "checklist": checklist, "plan": plan}

    def generate_code(self, spec_path, dry_run=False):
        result = self.run(spec_path)
        
        # Check for validation errors
        if result.get("type") == "schema_error":
            return result
        
        outputs = self.codegen.run(result["checklist"], dry_run=dry_run)
        
        if not dry_run:
            self.writer.write_all(outputs)
        
        return outputs

    def verify_checklist(self, checklist):
        return self.verifier.verify(checklist)
    
    def run_self_host(self, spec, dry_run=False, emit_preview=None):
        """
        Self-host mode: filter bootstrap items, emit to .selfhost_outputs/{fingerprint}/,
        write bootstrap_manifest.json with lineage and evidence.
        
        Args:
            spec: Product spec dict (should have self_host=true)
            dry_run: If True, return preview structure without writing files
            emit_preview: If provided, write preview JSON to this path
            
        Returns:
            dict with outputs, manifest, fingerprint
        """
        import hashlib
        from pathlib import Path
        
        # Build AST and checklist
        ast = self.ast.build(spec)
        checklist = self.checklist_gen.build(spec, ast=ast)
        
        # Filter bootstrap category items
        bootstrap_items = [
            item for item in checklist.get("items", [])
            if item.get("category") == "bootstrap"
        ]
        
        # Generate code for bootstrap items
        codegen_result = self.codegen.run({"items": bootstrap_items}, dry_run=True)
        
        # Compute fingerprint from spec content
        spec_str = json.dumps(spec, sort_keys=True)
        fingerprint = hashlib.sha256(spec_str.encode()).hexdigest()[:16]
        
        # Build output directory structure
        output_dir = Path(f".selfhost_outputs/{fingerprint}")
        
        # Prepare manifest
        manifest = {
            "fingerprint": fingerprint,
            "spec_metadata": spec.get("metadata", {}),
            "bootstrap_items": len(bootstrap_items),
            "codegen_bundle_hash": codegen_result.get("codegen_bundle_hash", "unknown"),
            "outputs": [out["path"] for out in codegen_result.get("outputs", [])]
        }
        
        preview = {
            "fingerprint": fingerprint,
            "output_dir": str(output_dir),
            "manifest": manifest,
            "modules": [out["path"] for out in codegen_result.get("outputs", [])],
            "codegen_bundle_hash": codegen_result.get("codegen_bundle_hash", "unknown"),
            "lineage": {
                "headers": checklist.get("lineage_headers", {})
            },
            "checklist": checklist.get("items", []),
            "outputs": codegen_result.get("outputs", [])
        }
        
        if dry_run:
            # Validate preview
            from shieldcraft.services.selfhost.preview_validator import validate_preview
            validation = validate_preview(preview)
            preview["validation_ok"] = validation["ok"]
            preview["validation_issues"] = validation["issues"]
            
            # Write preview if path provided
            if emit_preview:
                preview_path = Path(emit_preview)
                preview_path.parent.mkdir(parents=True, exist_ok=True)
                preview_path.write_text(json.dumps(preview, indent=2))
            
            return preview
        
        # Write files
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for output in codegen_result.get("outputs", []):
            file_path = output_dir / output["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(output["content"])
        
        # Write manifest
        manifest_path = output_dir / "bootstrap_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        
        return {
            "fingerprint": fingerprint,
            "output_dir": str(output_dir),
            "manifest": manifest,
            "outputs": codegen_result.get("outputs", [])
        }


    def generate_evidence(self, spec_path, checklist):
        canonical = self.det.canonicalize(checklist)
        checklist_hash = self.det.hash(canonical)
        prov = self.prov.build_record(
            spec_path=spec_path,
            engine_version="0.1.0",
            checklist_hash=checklist_hash
        )
        return self.evidence.build(
            checklist=checklist,
            provenance=prov,
            output_dir="evidence"
        )

    def execute(self, spec_path):
        # Load and validate
        spec = self.loader.load(spec_path)
        validation_result = self.validator.validate(spec)
        
        # Stop if invalid
        if not validation_result["valid"]:
            return {"type": "schema_error", "details": validation_result["errors"]}
        
        # Check for spec evolution
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        prev_spec_path = f"products/{product_id}/last_spec.json"
        spec_evolution = None
        
        if os.path.exists(prev_spec_path):
            from shieldcraft.services.spec.evolution import compute_evolution
            with open(prev_spec_path) as f:
                previous_spec = json.load(f)
            spec_evolution = compute_evolution(previous_spec, spec)
        
        # Build AST
        ast = self.ast.build(spec)
        
        # Create execution plan with spec for self-host detection
        plan = from_ast(ast, spec)
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        plan_dir = f"products/{product_id}"
        os.makedirs(plan_dir, exist_ok=True)
        write_canonical_json(f"{plan_dir}/plan.json", plan)
        
        # Run pipeline
        result = self.run(spec_path)
        if result.get("type") == "schema_error":
            return result
        
        # Extract checklist items from result
        checklist_data = result["checklist"]
        if isinstance(checklist_data, dict) and "items" in checklist_data:
            checklist_items = checklist_data["items"]
        elif isinstance(checklist_data, list):
            checklist_items = checklist_data
        else:
            # Unexpected format
            return {"type": "internal_error", "details": "Invalid checklist format"}
        
        # Generate code
        outputs = self.codegen.run(checklist_items)
        self.writer.write_all(outputs)
        
        # Bootstrap module emission for self-host
        if spec.get("metadata", {}).get("self_host") is True:
            # Collect bootstrap modules from checklist
            bootstrap_items = [item for item in checklist_items if item.get("classification") == "bootstrap"]
            
            if bootstrap_items:
                # Write bootstrap modules to .selfhost_outputs/modules/
                bootstrap_dir = ".selfhost_outputs/modules"
                os.makedirs(bootstrap_dir, exist_ok=True)
                
                bootstrap_outputs = []
                for item in bootstrap_items:
                    # Generate bootstrap code
                    item_id = item.get("id", "unknown")
                    module_name = item_id.replace(".", "_")
                    module_path = os.path.join(bootstrap_dir, f"{module_name}.py")
                    
                    # Use simple template for bootstrap
                    bootstrap_code = f"""# Bootstrap module: {item_id}
# Generated from: {item.get('ptr', 'unknown')}

class BootstrapModule:
    def __init__(self):
        self.id = "{item_id}"
    
    def execute(self):
        pass
"""
                    with open(module_path, "w") as f:
                        f.write(bootstrap_code)
                    
                    bootstrap_outputs.append({
                        "item_id": item_id,
                        "path": module_path
                    })
                
                # Emit bootstrap manifest
                bootstrap_manifest = {
                    "modules": bootstrap_outputs,
                    "count": len(bootstrap_outputs)
                }
                manifest_path = ".selfhost_outputs/bootstrap_manifest.json"
                with open(manifest_path, "w") as f:
                    json.dump(bootstrap_manifest, f, indent=2, sort_keys=True)
        
        # Generate evidence
        evidence = self.generate_evidence(spec_path, checklist_items)
        
        # Compute lineage bundle
        spec_fp = canonicalize(json.dumps(spec))
        items_fp = canonicalize(json.dumps(result["checklist"]))
        plan_fp = canonicalize(json.dumps(plan))
        code_fp = canonicalize(json.dumps(outputs))
        
        lineage_bundle = bundle(spec_fp, items_fp, plan_fp, code_fp)
        
        # Write manifest
        manifest_data = {
            "checklist": result["checklist"],
            "plan": plan,
            "evidence": evidence,
            "lineage": lineage_bundle,
            "outputs": outputs
        }
        write_manifest_v2(manifest_data, plan_dir)
        
        # Stability verification
        current_run = {
            "manifest": manifest_data,
            "signature": lineage_bundle["signature"]
        }
        
        # Compare with previous run if exists
        prev_manifest_path = f"{plan_dir}/manifest.json"
        stable = True
        if os.path.exists(prev_manifest_path):
            with open(prev_manifest_path) as f:
                prev_run = json.load(f)
            stable = compare(prev_run, current_run)
        
        # Compute spec metrics
        from shieldcraft.services.spec.metrics import compute_metrics
        checklist_items = result["checklist"].get("items", [])
        spec_metrics = compute_metrics(spec, ast, checklist_items)
        
        # Persist current spec as last_spec.json
        last_spec_path = f"products/{product_id}/last_spec.json"
        write_canonical_json(last_spec_path, spec)
        
        return {
            "checklist": result["checklist"],
            "generated": outputs,
            "evidence": evidence,
            "ast": ast,
            "plan": plan,
            "lineage": lineage_bundle,
            "stable": stable,
            "spec_evolution": spec_evolution,
            "spec_metrics": spec_metrics
        }
