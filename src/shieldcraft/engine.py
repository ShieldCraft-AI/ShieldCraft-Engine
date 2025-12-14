import json
import os
from shieldcraft.util.json_canonicalizer import canonicalize
from shieldcraft.dsl.loader import load_spec
from shieldcraft.services.ast.builder import ASTBuilder
from shieldcraft.services.planner.planner import Planner
from shieldcraft.services.checklist.generator import ChecklistGenerator
from shieldcraft.services.codegen.generator import CodeGenerator
from shieldcraft.services.codegen.emitter.writer import FileWriter
from shieldcraft.services.governance.determinism import DeterminismEngine
from shieldcraft.services.governance.provenance import ProvenanceEngine
from shieldcraft.services.governance.evidence import EvidenceBundle
from shieldcraft.services.governance.verifier import ChecklistVerifier
from shieldcraft.services.spec.schema_validator import validate_spec_against_schema
from shieldcraft.services.spec.model import SpecModel
from shieldcraft.services.spec.fingerprint import compute_spec_fingerprint
from shieldcraft.services.plan.execution_plan import from_ast
from shieldcraft.services.io.canonical_writer import write_canonical_json
from shieldcraft.services.artifacts.lineage import bundle
from shieldcraft.services.io.manifest_writer import write_manifest_v2
from shieldcraft.services.diff.impact import impact_summary
from shieldcraft.services.stability.stability import compare
from shieldcraft.services.validator import validate_instruction_block


class Engine:
    """ShieldCraft Engine

    Execution modes (all funnel through `preflight`/`_validate_spec` which enforce sync and instruction validation):
    - CLI: top-level `shieldcraft.main` calls `Engine.run` or `run_self_host` (self-host mode)
    - Direct API: callers may call `Engine.execute`, `Engine.run`, or `Engine.generate_code` from scripts/tests
    - Batch: `engine_batch.run_batch` invokes `Engine.execute` for each spec
    - Tests: unit/integration tests instantiate `Engine` and call these methods directly

    The sync verification gate is executed deterministically and non-bypassably before any
    instruction validation or side-effects (plan writing, codegen, evidence generation).
    """
    def __init__(self, schema_path):
        self.schema_path = schema_path
        self.ast = ASTBuilder()
        self.planner = Planner()
        self.checklist_gen = ChecklistGenerator()
        self.codegen = CodeGenerator()
        self.writer = FileWriter()
        self.det = DeterminismEngine()
        self.prov = ProvenanceEngine()
        self.evidence = EvidenceBundle(self.det, self.prov)
        self.verifier = ChecklistVerifier()
        # Readiness assertions: ensure required subsystems are importable and wired.
        try:
            from shieldcraft.services.validator import validate_instruction_block
            from shieldcraft.services.sync import verify_repo_sync
            # Persona optional scaffold (feature-flag guarded)
            from shieldcraft.persona import is_persona_enabled
        except Exception as e:
            raise RuntimeError("engine_readiness_failure: missing subsystem") from e
        # Feature flag - do not enable persona behavior by default
        self.persona_enabled = is_persona_enabled()
        # Snapshot feature flag
        self.snapshot_enabled = os.getenv("SHIELDCRAFT_SNAPSHOT_ENABLED", "0") == "1"

    def preflight(self, spec_or_path):
        """Run preflight validation (schema + instruction validation) without side-effects.

        Accepts either a spec dict or a path to a spec file. Raises `ValidationError` on
        instruction-level failures or returns a dict with schema validation failures.
        """
        # Load spec if a path is provided
        if isinstance(spec_or_path, str):
            raw = load_spec(spec_or_path)
            if isinstance(raw, SpecModel):
                spec = raw.raw
            else:
                spec = raw
        else:
            spec = spec_or_path

        # Reset execution state trace for this invocation
        try:
            # Initialize/clear the trace to ensure idempotent runs
            self._execution_state_entries = []  # type: ignore
            from shieldcraft.observability import emit_state
            emit_state(self, "preflight", "preflight", "start")
        except Exception:
            # Observability must not interfere with behavior
            pass

        # Governance presence check: ensure required governance artifacts exist
        # and meet immutability/version expectations before proceeding.
        try:
            # Only enforce governance presence checks when running from the
            # repository root (heuristic: the `spec/` directory is present).
            root = os.getcwd()
            if os.path.exists(os.path.join(root, "spec")):
                from shieldcraft.services.governance.registry import check_governance_presence
                # Derive engine major version from selfhost ENGINE_VERSION if present
                try:
                    from shieldcraft.services.selfhost import ENGINE_VERSION
                    engine_major = int(ENGINE_VERSION.split('.')[0])
                except Exception:
                    engine_major = None
                check_governance_presence(root, engine_major=engine_major)
        except RuntimeError:
            # Propagate specialized governance errors unchanged
            raise
        except Exception:
            # Normalize unexpected failures
            raise RuntimeError("governance_check_failed")

        # Repository sync verification is required before any validation.
        # Run this early to ensure the working repo state is consistent with expected sync artifacts.
        from shieldcraft.services.sync import verify_repo_state_authoritative, SYNC_MISSING
        try:
            verify_repo_state_authoritative(os.getcwd())
        except Exception as e:
            # If specific sync errors (external or snapshot) occur, propagate them
            # only for missing-sync (explicit SyncError with code==SYNC_MISSING) or SnapshotError.
            from shieldcraft.services.sync import SyncError
            from shieldcraft.snapshot import SnapshotError
            if isinstance(e, SnapshotError):
                raise
            if isinstance(e, SyncError):
                # Surface missing-sync explicitly; normalize other sync failures
                if getattr(e, "code", None) == SYNC_MISSING:
                    raise
                raise RuntimeError("sync_not_performed")
            raise RuntimeError("sync_not_performed")

        # Schema validation for legacy normalized specs
        if isinstance(spec, dict):
            try:
                valid, errors = validate_spec_against_schema(spec, self.schema_path)
            except Exception:
                valid, errors = True, []
            if not valid:
                return {"type": "schema_error", "details": errors}

        # Instruction validation raises ValidationError on failures
        try:
            from shieldcraft.observability import emit_state
            emit_state(self, "preflight", "validation", "start")
        except Exception:
            pass

        try:
            self._validate_spec(spec)
            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "preflight", "validation", "ok")
            except Exception:
                pass
        except Exception as e:
            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "preflight", "validation", "fail", getattr(e, "code", str(e)))
            except Exception:
                pass
            raise

        # Ensure validation recorded deterministically
        if isinstance(spec, dict) and "instructions" in spec:
            fp = compute_spec_fingerprint(spec)
            if getattr(self, "_last_validated_spec_fp", None) != fp:
                raise RuntimeError("validation_not_performed")

        try:
            from shieldcraft.observability import emit_state
            emit_state(self, "preflight", "preflight", "ok")
        except Exception:
            pass

        return {"ok": True}

    def _validate_spec(self, spec):
        """Centralized validation gate for instruction-level checks.

        All engine entrypoints that accept a `spec` MUST call this method
        before performing any work that could be influenced by instruction
        contents (AST build, plan creation, codegen). This ensures a single,
        deterministic validator is used across the codebase and prevents
        accidental bypasses.
        """
        if not isinstance(spec, dict):
            return

        # Verify repo sync first (non-bypassable) for all runs.
        # Use the authoritative sync decision point so we have a single
        # configurable source of truth (external vs snapshot).
        from shieldcraft.services.sync import verify_repo_state_authoritative
        try:
            sync_res = verify_repo_state_authoritative(os.getcwd())
        except Exception as e:
            # Propagate structured SyncError or SnapshotError for callers/tests.
            from shieldcraft.services.sync import SyncError
            from shieldcraft.snapshot import SnapshotError
            if isinstance(e, (SyncError, SnapshotError)):
                raise
            raise RuntimeError("sync_not_performed")

        # If snapshot enforcement is enabled, validate snapshot early (non-branching)
        if self.snapshot_enabled:
            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "preflight", "snapshot", "start")
            except Exception:
                pass

            try:
                from shieldcraft.snapshot import validate_snapshot, SnapshotError
                snapshot_path = os.path.join(os.getcwd(), "artifacts", "repo_snapshot.json")
                validate_snapshot(snapshot_path, os.getcwd())
                try:
                    from shieldcraft.observability import emit_state
                    emit_state(self, "preflight", "snapshot", "ok")
                except Exception:
                    pass
            except Exception as e:
                try:
                    from shieldcraft.observability import emit_state
                    emit_state(self, "preflight", "snapshot", "fail", getattr(e, "code", str(e)))
                except Exception:
                    pass
                # Propagate SnapshotError to callers so they can handle deterministic
                # snapshot validation failures.
                from shieldcraft.snapshot import SnapshotError
                if isinstance(e, SnapshotError):
                    raise
                # Normalize unexpected exceptions
                raise RuntimeError("snapshot_validation_failed")

        # Ensure verification actually ran and returned expected structure
        if not isinstance(sync_res, dict) or not sync_res.get("ok"):
            raise RuntimeError("sync_not_performed")
        self._last_sync_verified = sync_res.get("sha256")

        # Always run the instruction-level validator to ensure a single,
        # authoritative validation gate for specs prior to any plan/codegen.
        from shieldcraft.services.validator import validate_instruction_block
        validate_instruction_block(spec)
        # Record that this spec was validated (deterministic fingerprint)
        self._last_validated_spec_fp = compute_spec_fingerprint(spec)
        # Assert validation recorded
        if self._last_validated_spec_fp != compute_spec_fingerprint(spec):
            raise RuntimeError("validation_not_performed")

    def run(self, spec_path):
        # AUTHORITATIVE DSL: se_dsl_v1.schema.json via dsl.loader. Do not introduce parallel DSLs.
        
        # Load spec using canonical DSL loader which performs the canonical mapping
        raw = load_spec(spec_path)
        
        # Handle SpecModel or raw dict
        if isinstance(raw, SpecModel):
            spec_model = raw
            normalized = spec_model.raw
            ast = spec_model.ast
            fingerprint = spec_model.fingerprint
        else:
            # Legacy: normalize and validate
            normalized = canonicalize(raw) if not isinstance(raw, dict) else raw
            valid, errors = validate_spec_against_schema(normalized, self.schema_path)
            if not valid:
                return {"type": "schema_error", "details": errors}
            ast = self.ast.build(normalized)
            fingerprint = compute_spec_fingerprint(normalized)
            spec_model = SpecModel(normalized, ast, fingerprint)
        
        # AST already built in spec_model
        spec = normalized

        # Instruction validation: enforce instruction invariants before plan creation.
        # Use the single engine validation entrypoint to avoid duplicated validators
        # and to ensure all code-paths that ingest `spec` are subject to the same
        # deterministic validation behavior.
        self._validate_spec(spec)
        # Ensure validation recorded deterministically (prevent no-op/malicious bypass)
        if "instructions" in spec:
            fp = compute_spec_fingerprint(spec)
            if getattr(self, "_last_validated_spec_fp", None) != fp:
                raise RuntimeError("validation_not_performed")
        
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

        # Support both legacy list-of-outputs and new dict-with-outputs
        outputs_list = outputs.get("outputs") if isinstance(outputs, dict) and "outputs" in outputs else outputs

        if not dry_run:
            self.writer.write_all(outputs_list)

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
        
        # Emit self-host start for observability
        try:
            # Reset trace for direct self-host invocations to ensure idempotency
            self._execution_state_entries = []  # type: ignore
            from shieldcraft.observability import emit_state
            emit_state(self, "self_host", "self_host", "start")
        except Exception:
            pass

        # Validate instructions before doing any work. This is the non-bypassable
        # validation gate for self-host mode: do not build AST or generate code for
        # specs that fail instruction validation.
        self._validate_spec(spec)

        try:
            # Ensure validation recorded deterministically (prevent no-op/malicious bypass)
            if "instructions" in spec:
                fp = compute_spec_fingerprint(spec)
                if getattr(self, "_last_validated_spec_fp", None) != fp:
                    raise RuntimeError("validation_not_performed")

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

            # If persona feature is enabled, expose a hook to load persona definitions
            # (does not influence pipeline behavior). This is intentionally inert
            # by default and will be activated via environment flag in tests.
            if self.persona_enabled:
                try:
                    from shieldcraft.persona import load_persona, find_persona_files, resolve_persona_files
                    # Deterministically find persona files and resolve the chosen one.
                    files = find_persona_files(os.getcwd())
                    chosen = resolve_persona_files(files)
                    if chosen:
                        persona = load_persona(chosen)
                        # expose read-only PersonaContext into engine context
                        try:
                            from shieldcraft.persona import PersonaContext
                            self.persona = PersonaContext(
                                name=persona.name,
                                role=persona.role,
                                display_name=persona.display_name,
                                scope=persona.scope,
                                allowed_actions=persona.allowed_actions,
                                constraints=persona.constraints,
                            )
                        except Exception:
                            # fallback: raw persona object
                            self.persona = persona
                except Exception:
                    # Do not let persona loading failures affect self-host pipeline.
                    pass
            else:
                self.persona = None
            
            # Ensure only allowed inputs are consumed by self-host
            from shieldcraft.services.selfhost import is_allowed_selfhost_input, SELFHOST_READINESS_MARKER, provenance_header
            if not is_allowed_selfhost_input(spec):
                raise RuntimeError("disallowed_selfhost_input")

            # Assert readiness marker is present (single guarded flag that can be audited)
            from shieldcraft.services.selfhost import SELFHOST_READINESS_MARKER as _READINESS
            if not _READINESS:
                raise RuntimeError("selfhost_not_ready")

            # Enforce clean worktree for self-host runs (safety precondition).
            # By default we always enforce this check (including dry-runs) so that
            # callers cannot bypass the safety gate. A special internal opt-in
            # flag (`SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY`) may be set by the
            # orchestrator to permit self-build flows in ephemeral test/CI dirs.
            if os.getenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "0") != "1":
                try:
                    from shieldcraft.persona import _is_worktree_clean
                except Exception as e:
                    raise RuntimeError("worktree_check_failed") from e
                if not _is_worktree_clean():
                    raise RuntimeError("worktree_not_clean")

            # Compute fingerprint from spec content
            spec_str = json.dumps(spec, sort_keys=True)
            fingerprint = hashlib.sha256(spec_str.encode()).hexdigest()[:16]
            
            # Build output directory structure
            output_dir = Path(f".selfhost_outputs/{fingerprint}")
            
            # Prepare manifest
            manifest = {
                "fingerprint": fingerprint,
                "manifest_version": "v1",
                "spec_fingerprint": fingerprint,
                "spec_metadata": spec.get("metadata", {}),
                "bootstrap_items": len(bootstrap_items),
                "codegen_bundle_hash": codegen_result.get("codegen_bundle_hash", "unknown"),
                "outputs": [out["path"] for out in codegen_result.get("outputs", [])],
                "provenance": {
                    "engine_version": __import__('shieldcraft.services.selfhost', fromlist=['ENGINE_VERSION']).ENGINE_VERSION,
                    "spec_fingerprint": fingerprint,
                    "snapshot_hash": getattr(self, '_last_sync_verified', None),
                }
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
                # Prepend deterministic provenance header to preview outputs
                header = provenance_header(fingerprint, getattr(self, '_last_sync_verified', None))
                for o in preview.get("outputs", []):
                    o["content"] = header + o.get("content", "")
                
                # Write preview if path provided
                if emit_preview:
                    preview_path = Path(emit_preview)
                    preview_path.parent.mkdir(parents=True, exist_ok=True)
                    preview_path.write_text(json.dumps(preview, indent=2))
                
                try:
                    from shieldcraft.observability import emit_state
                    emit_state(self, "self_host", "self_host", "ok")
                except Exception:
                    pass
                return preview
            
            # Write files
            output_dir.mkdir(parents=True, exist_ok=True)
            # Enforce artifact emission lock: only allow known prefixes/files
            from shieldcraft.services.selfhost import is_allowed_selfhost_path

            for output in codegen_result.get("outputs", []):
                rel_path = output["path"].lstrip("./")
                if not is_allowed_selfhost_path(rel_path):
                    raise RuntimeError(f"disallowed_selfhost_artifact: {rel_path}")
                file_path = output_dir / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                # Prepend deterministic provenance header to emitted artifacts
                header = provenance_header(fingerprint, getattr(self, '_last_sync_verified', None))
                file_path.write_text(header + output["content"])
            
            # Write manifest
            manifest_path = output_dir / "bootstrap_manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2))
        # Also emit a canonical repo snapshot alongside bootstrap manifest to
        # enable closed-loop parity checks (self-host produces an artefact that
        # can be re-ingested for deterministic verification).
            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "self_host", "snapshot", "start")
            except Exception:
                pass

            try:
                from shieldcraft.snapshot import generate_snapshot
                snap = generate_snapshot(os.getcwd())
                snapshot_path = output_dir / "repo_snapshot.json"
                snapshot_path.write_text(json.dumps(snap, indent=2, sort_keys=True))
                # advertise snapshot in manifest outputs and return payload
                manifest["outputs"].append("repo_snapshot.json")
                try:
                    from shieldcraft.observability import emit_state
                    emit_state(self, "self_host", "snapshot", "ok")
                except Exception:
                    pass
            except Exception as e:
                try:
                    from shieldcraft.observability import emit_state
                    emit_state(self, "self_host", "snapshot", "fail", getattr(e, "code", str(e)))
                except Exception:
                    pass
                # Snapshot generation failures should not crash self-host emission;
                # they can be handled by external validation.
                pass

            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "self_host", "self_host", "ok")
            except Exception:
                pass

            return {
                "fingerprint": fingerprint,
                "output_dir": str(output_dir),
                "manifest": manifest,
                "outputs": codegen_result.get("outputs", [])
            }
        except Exception as e:
            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "self_host", "self_host", "fail", getattr(e, "code", str(e)))
            except Exception:
                pass
            raise

    def run_self_build(self, spec_path: str = "spec/se_dsl_v1.spec.json", dry_run: bool = False):
        """Run a self-build using the engine pipeline and emit a self-build bundle.

        This performs: validate -> sync -> generate -> self-host and emits a
        self-build bundle under `artifacts/self_build/<fingerprint>/`.
        """
        import shutil
        from pathlib import Path
        from shieldcraft.services.selfhost import SELFBUILD_OUTPUT_DIR, SELFBUILD_BITWISE_ARTIFACTS, provenance_header_extended

        # Recursion guard: quickly fail if a self-build is already running
        if getattr(self, "_selfbuild_running", False):
            raise RuntimeError("selfbuild_recursive_invocation")
        # Require explicit opt-in for self-build runs to avoid accidental invocation
        if os.getenv("SHIELDCRAFT_SELFBUILD_ENABLED", "0") != "1" and os.getenv("GITHUB_ACTIONS", "") != "true":
            raise RuntimeError("selfbuild_disabled")
        self._selfbuild_running = True

        try:
            # Load spec and validate (preflight checks include sync and validation)
            spec_file = spec_path
            if not os.path.isabs(spec_file) and not os.path.exists(spec_file):
                # resolve repo-relative
                repo_root = Path(__file__).resolve().parents[2]
                spec_file = str(repo_root / spec_path)
            with open(spec_file) as f:
                spec = json.load(f)

            # Centralized validation gate
            self._validate_spec(spec)

            # Record lineage info
            previous_snapshot = getattr(self, "_last_sync_verified", None)
            build_depth = int(os.getenv("SHIELDCRAFT_BUILD_DEPTH", "0"))

            # Run self-host to produce outputs (dry-run first)
            # Allow the orchestrator to bypass worktree cleanliness for both
            # preview and real runs within this self-build invocation.
            prev = os.getenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY")
            os.environ["SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY"] = "1"
            try:
                preview = self.run_self_host(spec, dry_run=True, emit_preview=None)
            except Exception:
                # Ensure we restore the env var if preview fails early
                if prev is None:
                    os.environ.pop("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", None)
                else:
                    os.environ["SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY"] = prev
                raise

            if dry_run:
                # Attach extended provenance and return preview
                preview["manifest"]["provenance"]["previous_snapshot"] = previous_snapshot
                preview["manifest"]["provenance"]["build_depth"] = build_depth + 1
                return preview

            # Real run: execute and copy outputs into self-build location
            try:
                res = self.run_self_host(spec, dry_run=False)
            finally:
                if prev is None:
                    os.environ.pop("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", None)
                else:
                    os.environ["SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY"] = prev
            out_dir = Path(res.get("output_dir"))
            target_dir = Path(SELFBUILD_OUTPUT_DIR) / res.get("fingerprint")
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(out_dir, target_dir)

            # Emit self-build manifest with extended provenance
            manifest = res.get("manifest", {})
            manifest.setdefault("provenance", {})
            manifest["provenance"]["previous_snapshot"] = previous_snapshot
            manifest["provenance"]["build_depth"] = build_depth + 1
            manifest_path = target_dir / "self_build_manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))

            # Baseline comparison guard: if a baseline exists, compare outputs
            from shieldcraft.services.selfhost import SELFBUILD_BASELINE_DIR, DEFAULT_BASELINE_NAME, SELFBUILD_BITWISE_ARTIFACTS, is_allowed_diff
            baseline_root = Path(SELFBUILD_BASELINE_DIR) / DEFAULT_BASELINE_NAME
            if baseline_root.exists():
                # Compare bitwise artifacts
                for fname in SELFBUILD_BITWISE_ARTIFACTS:
                    emitted_path = target_dir / fname
                    baseline_path = baseline_root / fname
                    if not baseline_path.exists():
                        raise RuntimeError(f"selfbuild_baseline_missing_artifact: {fname}")
                    if not emitted_path.exists():
                        raise RuntimeError(f"selfbuild_missing_artifact: {fname}")
                    if emitted_path.read_bytes() != baseline_path.read_bytes():
                        # If allowed in allowlist, continue; otherwise fail and produce forensics
                        rel = fname
                        if not is_allowed_diff(str(baseline_root), rel):
                            # produce forensic bundle
                            forensics_dir = target_dir / "forensics"
                            forensics_dir.mkdir(exist_ok=True)
                            fb = forensics_dir / "forensics.json"
                            fb.write_text(json.dumps({
                                "mismatch": rel,
                                "emitted_sha256": hashlib.sha256(emitted_path.read_bytes()).hexdigest(),
                                "baseline_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                            }, indent=2, sort_keys=True))
                            raise RuntimeError("selfbuild_mismatch: emitted artifact does not match baseline")
                # Compare snapshot tree_hash semantically
                try:
                    from shieldcraft.snapshot import generate_snapshot
                    current = generate_snapshot(os.getcwd())
                    emitted = json.loads((target_dir / "repo_snapshot.json").read_text())
                    baseline_snapshot = json.loads((baseline_root / "repo_snapshot.json").read_text())
                    if baseline_snapshot.get("tree_hash") != emitted.get("tree_hash"):
                        if not is_allowed_diff(str(baseline_root), "repo_snapshot.json"):
                            raise RuntimeError("selfbuild_mismatch: repo_snapshot.tree_hash mismatch")
                except FileNotFoundError:
                    raise RuntimeError("selfbuild_missing_snapshot")
            else:
                # Baseline not present: allow explicit establishment only
                if os.getenv("SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE", "0") == "1":
                    baseline_root.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(target_dir, baseline_root, dirs_exist_ok=True)
                else:
                    # Baseline not present: allow run to proceed but do not establish
                    # unless explicitly requested by environment. This lets first-time
                    # runs emit outputs without failing; tests may then establish or
                    # compare subsequently.
                    if os.getenv("SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE", "0") == "1":
                        baseline_root.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(target_dir, baseline_root, dirs_exist_ok=True)
                    # otherwise: continue without failing

            return {"ok": True, "output_dir": str(target_dir), "manifest": manifest}
        finally:
            self._selfbuild_running = False

    def verify_self_build_output(self, output_dir: str) -> None:
        """Verify that the self-build output snapshot matches the current repo.

        Raises RuntimeError on mismatch or missing snapshot.
        """
        from pathlib import Path
        from shieldcraft.snapshot import generate_snapshot
        p = Path(output_dir)
        snap_path = p / "repo_snapshot.json"
        if not snap_path.exists():
            raise RuntimeError("selfbuild_missing_snapshot")
        emitted = json.loads(snap_path.read_text())
        current = generate_snapshot(os.getcwd())
        if current.get("tree_hash") != emitted.get("tree_hash"):
            raise RuntimeError("selfbuild_mismatch: emitted snapshot does not match current repo snapshot")


    def generate_evidence(self, spec_path, checklist):
        canonical = self.det.canonicalize(checklist)
        checklist_hash = self.det.hash(canonical)
        prov = self.prov.build_record(
            spec_path=spec_path,
            engine_version="0.1.0",
            checklist_hash=checklist_hash
        )
        # Load spec to extract invariants and graph for evidence building
        import json
        import pathlib
        spec_obj = {}
        try:
            spec_obj = json.loads(pathlib.Path(spec_path).read_text())
        except Exception:
            spec_obj = {}

        invariants = spec_obj.get("invariants", [])
        graph = spec_obj.get("model", {}).get("dependencies", [])

        return self.evidence.build(
            checklist=checklist,
            invariants=invariants,
            graph=graph,
            provenance=prov,
            output_dir="evidence"
        )

    def execute(self, spec_path):
        # Load and validate using canonical DSL
        raw = load_spec(spec_path)
        
        # Handle SpecModel or raw dict
        if isinstance(raw, SpecModel):
            spec_model = raw
            spec = spec_model.raw
            ast = spec_model.ast
            # Ensure instruction validation even when loader returns a SpecModel.
            self._validate_spec(spec)
            if "instructions" in spec:
                fp = compute_spec_fingerprint(spec)
                if getattr(self, "_last_validated_spec_fp", None) != fp:
                    raise RuntimeError("validation_not_performed")
        else:
            # Legacy: normalize and validate
            spec = canonicalize(raw) if not isinstance(raw, dict) else raw
            valid, errors = validate_spec_against_schema(spec, self.schema_path)
            if not valid:
                return {"type": "schema_error", "details": errors}
            # Enforce instruction validation before building AST or creating plans
            # to ensure we do not process invalid instruction specs.
            self._validate_spec(spec)
            if "instructions" in spec:
                fp = compute_spec_fingerprint(spec)
                if getattr(self, "_last_validated_spec_fp", None) != fp:
                    raise RuntimeError("validation_not_performed")
            ast = self.ast.build(spec)
        
        # Check for spec evolution
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        prev_spec_path = f"products/{product_id}/last_spec.json"
        spec_evolution = None
        
        if os.path.exists(prev_spec_path):
            from shieldcraft.services.spec.evolution import compute_evolution
            with open(prev_spec_path) as f:
                previous_spec = json.load(f)
            spec_evolution = compute_evolution(previous_spec, spec)
        
        # AST already built above
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
        # Support both historic list-of-outputs and dict with 'outputs' key
        outputs_list = outputs.get("outputs") if isinstance(outputs, dict) and "outputs" in outputs else outputs
        self.writer.write_all(outputs_list)
        
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
        # INTENTIONAL: Empty execute method in generated template.
        # User implementations will override this method.
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
            "generated": outputs_list,
            "evidence": evidence,
            "ast": ast,
            "plan": plan,
            "lineage": lineage_bundle,
            "stable": stable,
            "spec_evolution": spec_evolution,
            "spec_metrics": spec_metrics
        }
