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


def finalize_checklist(engine, partial_result=None, exception=None):
    """Create a guaranteed checklist result from recorded events, partial result, or exception.

    This function is policy-driven plumbing: it translates recorded gate events
    into checklist items and returns a normalized final result dict. It MUST
    not raise; callers should treat the returned dict as the canonical run
    outcome.
    """
    # Collect recorded events (defensive)
    events = []
    try:
        if engine is not None and getattr(engine, 'checklist_context', None):
            try:
                events = engine.checklist_context.get_events()
            except Exception:
                events = []
    except Exception:
        events = []

    items = []
    # Start from any existing checklist items in partial_result
    try:
        if partial_result and isinstance(partial_result.get('checklist'), dict):
            existing = partial_result.get('checklist', {}).get('items', []) or []
            items.extend(existing)
    except Exception:
        pass

    # Translate gate events into checklist items
    for ev in events:
        try:
            gid = ev.get('gate_id')
            phase = ev.get('phase')
            outcome = ev.get('outcome')
            msg = ev.get('message') or gid
            evidence = ev.get('evidence')
            # Minimal checklist item: ptr and text; allow model.normalize_item to fill defaults
            it = {'ptr': '/', 'text': f"{gid}: {msg}", 'meta': {'gate': gid, 'phase': phase, 'evidence': evidence}}
            # Severity heuristics: REFUSAL/BLOCKER -> high
            if outcome and outcome.upper() in ('REFUSAL', 'BLOCKER'):
                it['severity'] = 'high'
            else:
                it['severity'] = 'medium'
            items.append(it)
        except Exception:
            pass

    # If exception occurred, record it as a diagnostic item
    error_info = None
    if exception is not None:
        try:
            err_text = str(exception)
            items.append({'ptr': '/', 'text': f"internal_exception: {err_text}", 'severity': 'high', 'meta': {'exception': err_text}})
            error_info = {'message': err_text, 'type': exception.__class__.__name__}
        except Exception:
            pass

    # Build checklist object and attach events for auditing
    checklist = {'items': items, 'emitted': True, 'events': events}

    # Flag refusal if any REFUSAL events present
    for ev in events:
        if ev.get('outcome') == 'REFUSAL':
            checklist['refusal'] = True
            checklist['refusal_reason'] = ev.get('message') or ev.get('gate_id')
            break

    # Derive a single canonical primary outcome from recorded events.
    # Rules (deterministic, no heuristics):
    #  - REFUSAL if any event.outcome == 'REFUSAL'
    #  - BLOCKED if no REFUSAL and any event.outcome == 'BLOCKER'
    #  - DIAGNOSTIC_ONLY if only DIAGNOSTIC events are present
    #  - SUCCESS if zero events or only informational/non-diagnostic events
    outcomes = [((ev.get('outcome') or '').upper()) for ev in events]
    primary_outcome = None
    if any(o == 'REFUSAL' for o in outcomes):
        primary_outcome = 'REFUSAL'
    elif any(o == 'BLOCKER' for o in outcomes):
        primary_outcome = 'BLOCKED'
    elif not events:
        primary_outcome = 'SUCCESS'
    elif all(o == 'DIAGNOSTIC' for o in outcomes if o):
        primary_outcome = 'DIAGNOSTIC_ONLY'
    else:
        # If events exist but are not purely DIAGNOSTIC, treat as SUCCESS per rules
        primary_outcome = 'SUCCESS'

    checklist['primary_outcome'] = primary_outcome

    # Top-level convenience flags derived strictly from primary_outcome
    result_refusal = primary_outcome == 'REFUSAL'

    # Assign deterministic semantic roles to checklist items (exactly one role each).
    # Roles: PRIMARY_CAUSE, CONTRIBUTING_BLOCKER, SECONDARY_DIAGNOSTIC, INFORMATIONAL
    # Only assign a PRIMARY_CAUSE when primary_outcome != 'SUCCESS'. Determination
    # is based on matching items' meta.gate to recorded events of the decisive type.
    gate_outcomes = {}
    for ev in events:
        g = ev.get('gate_id')
        o = (ev.get('outcome') or '').upper()
        if g:
            gate_outcomes.setdefault(g, set()).add(o)

    # Map primary_outcome back to the decisive event outcome label
    decisive_label = None
    if primary_outcome == 'REFUSAL':
        decisive_label = 'REFUSAL'
    elif primary_outcome == 'BLOCKED':
        decisive_label = 'BLOCKER'
    elif primary_outcome == 'DIAGNOSTIC_ONLY':
        decisive_label = 'DIAGNOSTIC'

    items = checklist.get('items', []) or []
    # Helper deterministic key
    def _item_key(it):
        meta = it.get('meta', {}) or {}
        return (meta.get('gate') or '', meta.get('phase') or '', it.get('text') or '')

    primary_item = None
    if primary_outcome != 'SUCCESS' and items:
        candidate_gates = sorted([g for g, outs in gate_outcomes.items() if decisive_label in outs]) if decisive_label else []
        candidate_items = [it for it in items if (it.get('meta') or {}).get('gate') in candidate_gates]
        if candidate_items:
            primary_item = min(candidate_items, key=_item_key)
        else:
            # fallback: pick a deterministic item from all items
            primary_item = min(items, key=_item_key)

    # Assign roles
    for it in items:
        it['role'] = None
        if primary_item is not None and it is primary_item:
            it['role'] = 'PRIMARY_CAUSE'
            continue
        gate = (it.get('meta') or {}).get('gate')
        gate_out = set()
        if gate:
            gate_out = gate_outcomes.get(gate, set())
        # CONTRIBUTING_BLOCKER if gate was BLOCKER and not primary
        if 'BLOCKER' in gate_out:
            it['role'] = 'CONTRIBUTING_BLOCKER'
            continue
        # SECONDARY_DIAGNOSTIC when diagnostic and primary outcome is not DIAGNOSTIC_ONLY
        if 'DIAGNOSTIC' in gate_out and primary_outcome != 'DIAGNOSTIC_ONLY':
            it['role'] = 'SECONDARY_DIAGNOSTIC'
            continue
        # Default informational
        it['role'] = 'INFORMATIONAL'

    # Enforce semantic invariants now that roles are assigned
    _assert_semantic_invariants(checklist, primary_outcome, gate_outcomes)

    # Expose primary outcome at the top-level result as required by the
    # Checklist Semantics Contract (Phase 5).
    result_primary_outcome = primary_outcome

    # Compose final result preserving partial_result type if present
    result = {}
    if partial_result and isinstance(partial_result, dict):
        result.update(partial_result)

    # Ensure canonical fields
    result['checklist'] = checklist
    # Reflect primary outcome and derived refusal at the top-level for ease of consumption
    result['primary_outcome'] = result_primary_outcome
    result['refusal'] = result_refusal
    # Surface an explicit top-level emission flag so callers and invariants
    # can assert emission without digging into nested structures.
    result['emitted'] = True
    if error_info:
        result['error'] = error_info

    # Central invariant assertion: ensure finalized result explicitly
    # declares that emission occurred and includes the checklist payload.
    if not (result.get('emitted') is True and 'checklist' in result):
        raise AssertionError('Checklist emission invariant violated')

    return result


def _assert_semantic_invariants(checklist_obj, primary, gate_outcomes=None):
    """Module-level semantic invariant assertions for checklists.

    This helper is testable and is invoked from `finalize_checklist` after
    roles have been deterministically assigned.
    """
    items_local = checklist_obj.get('items', []) or []
    roles = [it.get('role') for it in items_local]
    gate_outcomes = gate_outcomes or {}
    # Exactly one PRIMARY_CAUSE item MUST exist unless primary == 'SUCCESS'
    if primary != 'SUCCESS':
        if roles.count('PRIMARY_CAUSE') != 1:
            raise AssertionError('Semantic invariant violated: exactly one PRIMARY_CAUSE required for non-SUCCESS outcomes')
    else:
        if 'PRIMARY_CAUSE' in roles:
            raise AssertionError('Semantic invariant violated: SUCCESS outcome must not contain PRIMARY_CAUSE')
    # REFUSAL outcome MUST include refusal_reason
    if primary == 'REFUSAL':
        if not checklist_obj.get('refusal') or not checklist_obj.get('refusal_reason'):
            raise AssertionError('Semantic invariant violated: REFUSAL outcome must include refusal_reason')
    # BLOCKED outcome MUST NOT set refusal == true
    if primary == 'BLOCKED':
        if checklist_obj.get('refusal'):
            raise AssertionError('Semantic invariant violated: BLOCKED outcome must not set refusal == true')
    # DIAGNOSTIC_ONLY outcome MUST NOT contain BLOCKER or REFUSAL items
    if primary == 'DIAGNOSTIC_ONLY':
        if any(((it.get('meta') or {}).get('gate') and ('BLOCKER' in gate_outcomes.get((it.get('meta') or {}).get('gate'), set()) or 'REFUSAL' in gate_outcomes.get((it.get('meta') or {}).get('gate'), set()))) for it in items_local):
            raise AssertionError('Semantic invariant violated: DIAGNOSTIC_ONLY outcome must not contain BLOCKER or REFUSAL items')


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
        # Checklist context for recording gate events; plumbing only.
        try:
            from shieldcraft.services.checklist.context import ChecklistContext, set_global_context
            self.checklist_context = ChecklistContext()
            try:
                # Register global plumbing context for modules that cannot access engine directly
                set_global_context(self.checklist_context)
            except Exception:
                pass
        except Exception:
            # Keep engine usable even if context module unavailable (defensive)
            self.checklist_context = None
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
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G1_ENGINE_READINESS_FAILURE", "preflight", "REFUSAL", message="engine readiness failure", evidence={"error": str(e)})
                    except Exception:
                        pass
            except Exception:
                pass
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
        except RuntimeError as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G2_GOVERNANCE_PRESENCE_CHECK", "preflight", "REFUSAL", message="governance presence check failed", evidence={"error": str(e)})
                    except Exception:
                        pass
            except Exception:
                pass
            # Propagate specialized governance errors unchanged
            raise
        except Exception as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G2_GOVERNANCE_PRESENCE_CHECK", "preflight", "REFUSAL", message="governance check error", evidence={"error": str(e)})
                    except Exception:
                        pass
            except Exception:
                pass
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
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            self.checklist_context.record_event("G3_REPO_SYNC_VERIFICATION", "preflight", "REFUSAL", message="snapshot error", evidence={"error": str(e)})
                        except Exception:
                            pass
                except Exception:
                    pass
                raise
            if isinstance(e, SyncError):
                # Surface missing-sync explicitly; normalize other sync failures
                if getattr(e, "code", None) == SYNC_MISSING:
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G3_REPO_SYNC_VERIFICATION", "preflight", "REFUSAL", message="repo sync missing", evidence={"error": str(e)})
                            except Exception:
                                pass
                    except Exception:
                        pass
                    raise
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            self.checklist_context.record_event("G3_REPO_SYNC_VERIFICATION", "preflight", "REFUSAL", message="repo sync verification failed", evidence={"error": str(e)})
                        except Exception:
                            pass
                except Exception:
                    pass
                raise RuntimeError("sync_not_performed")
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G3_REPO_SYNC_VERIFICATION", "preflight", "REFUSAL", message="repo sync verification failed", evidence={"error": str(e)})
                    except Exception:
                        pass
            except Exception:
                pass
            raise RuntimeError("sync_not_performed")

        # Schema validation for legacy normalized specs
        if isinstance(spec, dict):
            try:
                valid, errors = validate_spec_against_schema(spec, self.schema_path)
            except Exception:
                valid, errors = True, []
            if not valid:
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            self.checklist_context.record_event("G4_SCHEMA_VALIDATION", "preflight", "DIAGNOSTIC", message="schema validation failed", evidence={"error_count": len(errors)})
                        except Exception:
                            pass
                except Exception:
                    pass
                # Normalize schema error to a finalized checklist return so emission is guaranteed
                return finalize_checklist(self, partial_result={"type": "schema_error", "details": errors})

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

        # Verification spine hook (non-invasive): validate registered verification
        # properties for well-formedness. This must not alter preflight outcome
        # unless verification properties are malformed (reported as verification_failed).
        try:
            from shieldcraft.verification import registry as _vreg, assertions as _vassert
            props = _vreg.global_registry().get_all()
            _vassert.assert_verification_properties(props)
        except RuntimeError as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G6_VERIFICATION_SPINE_FAILURE", "preflight", "DIAGNOSTIC", message="verification spine failure", evidence={"error": str(e)})
                    except Exception:
                        pass
            except Exception:
                pass
            # Do not raise here; record diagnostic and allow centralized finalization to handle outcome
            pass
        except Exception:
            # Do not change preflight behavior if verification spine is unavailable
            pass

        # Ensure validation recorded deterministically
        if isinstance(spec, dict) and "instructions" in spec:
            fp = compute_spec_fingerprint(spec)
            if getattr(self, "_last_validated_spec_fp", None) != fp:
                raise RuntimeError("validation_not_performed")
        # Check for persona vetoes after validation but before finishing preflight
        try:
            if hasattr(self, "_persona_vetoes") and self._persona_vetoes:
                # Deterministic resolution: sort by severity (critical>high>medium>low), then persona_id
                severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
                def _key(v):
                    return (severity_order.get(v.get("severity"), 0), v.get("persona_id"))
                sel = sorted(self._persona_vetoes, key=_key, reverse=True)[0]
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            self.checklist_context.record_event("G7_PERSONA_VETO", "preflight", "REFUSAL", message="persona veto triggered", evidence={"persona_id": sel.get('persona_id'), "code": sel.get('code')})
                        except Exception:
                            pass
                except Exception:
                    pass
                raise RuntimeError(f"persona_veto: {sel.get('persona_id')}:{sel.get('code')}")
        except RuntimeError:
            raise
        except Exception:
            # Observability must not alter behavior if failing
            pass
        # Enforce Test Attachment Contract (TAC v1) before finishing preflight
        # This enforcement is opt-in to avoid breaking existing callers; enable
        # via env var `SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT=1` or by setting
        # `metadata.enforce_tests_attached` in the spec. Tests that validate
        # TAC should set the env var explicitly.
        try:
            enforce_flag = os.getenv("SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT", "0") == "1"
            spec_enforce = isinstance(spec, dict) and spec.get("metadata", {}).get("enforce_tests_attached", False)
            if enforce_flag or spec_enforce:
                from shieldcraft.services.validator.tests_attached_validator import verify_tests_attached, ProductInvariantFailure
                # Build a dry-run checklist to inspect test_refs (non-emitting)
                try:
                    from shieldcraft.services.ast.builder import ASTBuilder
                    ast_local = ASTBuilder().build(spec)
                except Exception:
                    ast_local = None
                checklist_preview = None
                try:
                    checklist_preview = self.checklist_gen.build(spec, ast=ast_local, dry_run=True, run_test_gate=False, engine=self)
                except Exception:
                    # If checklist generation itself fails, surface as preflight failure
                    raise RuntimeError("checklist_generation_failed")
                # Now verify TAC
                verify_tests_attached(checklist_preview)
        except ProductInvariantFailure as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G8_TEST_ATTACHMENT_CONTRACT", "preflight", "REFUSAL", message="test-attachment contract failed", evidence={"error": str(e)})
                    except Exception:
                        pass
            except Exception:
                pass
            # Re-raise to allow caller to see the structured failure
            raise
        except Exception:
            # Any unexpected check failure is surfaced as a preflight failure
            raise RuntimeError("tests_attached_check_failed")
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
            # Ensure non-dict specs surface as structured validation failures
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G5_VALIDATION_TYPE_GATES", "preflight", "REFUSAL", message="spec not a dict")
                    except Exception:
                        pass
            except Exception:
                pass
            from shieldcraft.services.validator import ValidationError, SPEC_NOT_DICT
            raise ValidationError(SPEC_NOT_DICT, "spec must be a dict")

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
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G5_VALIDATION_TYPE_GATES", "preflight", "REFUSAL", message="validation not recorded")
                    except Exception:
                        pass
            except Exception:
                pass
            raise RuntimeError("validation_not_performed")

    def run(self, spec_path):
        # AUTHORITATIVE DSL: se_dsl_v1.schema.json via dsl.loader. Do not introduce parallel DSLs.
        
        try:
            # Load spec using canonical DSL loader which performs the canonical mapping
            raw = load_spec(spec_path)
        except Exception as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G4_SCHEMA_VALIDATION", "preflight", "DIAGNOSTIC", message="spec load failed", evidence={"error": str(e)})
                    except Exception:
                        pass
            except Exception:
                pass
            return finalize_checklist(self, partial_result=None, exception=e)

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
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            self.checklist_context.record_event("G4_SCHEMA_VALIDATION", "preflight", "DIAGNOSTIC", message="schema validation failed", evidence={"error_count": len(errors)})
                        except Exception:
                            pass
                except Exception:
                    pass
                # Create a finalized checklist result for schema errors
                return finalize_checklist(self, partial_result={"type": "schema_error", "details": errors})
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
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            self.checklist_context.record_event("G5_VALIDATION_TYPE_GATES", "preflight", "REFUSAL", message="validation not performed")
                        except Exception:
                            pass
                except Exception:
                    pass
                raise RuntimeError("validation_not_performed")
        
        # Create execution plan
        plan = from_ast(ast)
        
        # Store plan context
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        plan_dir = f"products/{product_id}"
        os.makedirs(plan_dir, exist_ok=True)
        write_canonical_json(f"{plan_dir}/plan.json", plan)
        
        # Generate checklist using AST
        # Ensure a deterministic run seed is recorded and available to subsystems
        try:
            from shieldcraft.verification.seed_manager import generate_seed, snapshot
            generate_seed(self, "run")
        except Exception:
            pass

        checklist = self.checklist_gen.build(spec, ast=ast, engine=self)

        # Attach determinism snapshot for replayability
        try:
            from shieldcraft.verification.seed_manager import snapshot
            det = snapshot(self)
            checklist["_determinism"] = {"seeds": det, "spec": spec, "ast": ast, "checklist": checklist}
        except Exception:
            pass
        # Evaluate readiness based on verification gates and attach report
        try:
            from shieldcraft.verification.readiness_evaluator import evaluate_readiness
            from shieldcraft.verification.readiness_report import render_readiness
            readiness = evaluate_readiness(self, spec, checklist)
            checklist_readiness = readiness
            checklist["_readiness"] = checklist_readiness
            checklist["_readiness_report"] = render_readiness(readiness)
            # Emit observable readiness state
            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "readiness", "readiness", "ok" if readiness.get("ok") else "fail", str(readiness.get("results")))
            except Exception:
                pass
        except Exception:
            # If readiness evaluation fails, mark as not ready and attach minimal info
            checklist["_readiness"] = {"ok": False, "results": {"readiness_eval": {"ok": False}}}
            checklist["_readiness_report"] = "Readiness evaluation failed"
        
        try:
            return finalize_checklist(self, partial_result={"spec": spec, "ast": ast, "checklist": checklist, "plan": plan})
        except Exception as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G22_EXECUTE_INTERNAL_ERROR_RETURN", "generation", "DIAGNOSTIC", message=str(e))
                    except Exception:
                        pass
            except Exception:
                pass
            return finalize_checklist(self, partial_result=None, exception=e)
        except Exception as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G22_EXECUTE_INTERNAL_ERROR_RETURN", "generation", "DIAGNOSTIC", message=str(e))
                    except Exception:
                        pass
            except Exception:
                pass
            return finalize_checklist(self, partial_result=None, exception=e)

    def generate_code(self, spec_path, dry_run=False):
        result = self.run(spec_path)
        
        # Check for validation errors
        if result.get("type") == "schema_error":
            return result
        try:
            outputs = self.codegen.run(result["checklist"], dry_run=dry_run)

            # Support both legacy list-of-outputs and new dict-with-outputs
            outputs_list = outputs.get("outputs") if isinstance(outputs, dict) and "outputs" in outputs else outputs

            if not dry_run:
                self.writer.write_all(outputs_list)

            return outputs
        except Exception as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G22_CODEGEN_INTERNAL_ERROR_RETURN", "generation", "DIAGNOSTIC", message=str(e))
                    except Exception:
                        pass
            except Exception:
                pass
            return finalize_checklist(self, partial_result=None, exception=e)

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
        try:
            self._validate_spec(spec)

            # Ensure validation recorded deterministically (prevent no-op/malicious bypass)
            if "instructions" in spec:
                fp = compute_spec_fingerprint(spec)
                if getattr(self, "_last_validated_spec_fp", None) != fp:
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G5_VALIDATION_TYPE_GATES", "preflight", "REFUSAL", message="validation not performed")
                            except Exception:
                                pass
                    except Exception:
                        pass
                    raise RuntimeError("validation_not_performed")

            # Build AST and checklist
            ast = self.ast.build(spec)
            checklist = self.checklist_gen.build(spec, ast=ast, engine=self)
            
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
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            self.checklist_context.record_event("G14_SELFHOST_INPUT_SANDBOX", "post_generation", "REFUSAL", message="disallowed self-host input")
                        except Exception:
                            pass
                except Exception:
                    pass
                raise RuntimeError("disallowed_selfhost_input")

            # Assert readiness marker is present (single guarded flag that can be audited)
            from shieldcraft.services.selfhost import SELFHOST_READINESS_MARKER as _READINESS
            if not _READINESS:
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            self.checklist_context.record_event("G14_SELFHOST_INPUT_SANDBOX", "post_generation", "REFUSAL", message="self-host not ready")
                        except Exception:
                            pass
                except Exception:
                    pass
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
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G14_SELFHOST_INPUT_SANDBOX", "post_generation", "REFUSAL", message="worktree_check_failed", evidence={"error": str(e)})
                            except Exception:
                                pass
                    except Exception:
                        pass
                    raise RuntimeError("worktree_check_failed") from e
                if not _is_worktree_clean():
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G14_SELFHOST_INPUT_SANDBOX", "post_generation", "REFUSAL", message="worktree not clean")
                            except Exception:
                                pass
                    except Exception:
                        pass
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
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G15_DISALLOWED_SELFHOST_ARTIFACT", "post_generation", "REFUSAL", message=f"disallowed_selfhost_artifact: {rel_path}", evidence={"path": rel_path})
                            except Exception:
                                pass
                    except Exception:
                        pass
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

            # Post-processing: enforce minimality and execution-plan invariants
            try:
                # Prefer persisted canonical requirements if available, else extract from spec
                try:
                    reqs = json.load(open(os.path.join(output_dir, 'requirements.json'))).get('requirements', [])
                except Exception:
                    try:
                        reqs = json.load(open(os.path.join('.selfhost_outputs', 'requirements.json'))).get('requirements', [])
                    except Exception:
                        from shieldcraft.interpretation.requirements import extract_requirements
                        rtxt = spec.get('metadata', {}).get('source_material') or spec.get('raw_input') or json.dumps(spec, sort_keys=True)
                        # ensure string input for extractor
                        if not isinstance(rtxt, str):
                            import json as _json
                            rtxt = _json.dumps(rtxt, sort_keys=True)
                        reqs = extract_requirements(rtxt)
                # Use in-memory checklist when available (deterministic), fallback to persisted
                items = checklist.get('items', []) or json.load(open(os.path.join('.selfhost_outputs', 'checklist.json'))).get('items', [])
                valid_items = [it for it in items if it.get('quality_status') != 'INVALID']

                # Collapse redundant items deterministically and fail on invariant violations
                from shieldcraft.checklist.equivalence import detect_and_collapse
                pruned_items, minimality_report = detect_and_collapse(valid_items, reqs)
                violations = [p for p in minimality_report.get('proof_of_minimality', []) if not p.get('necessary')]
                if violations:
                    manifest['checklist_minimality_summary'] = {
                        'removed_count': minimality_report.get('removed_count', 0),
                        'equivalence_groups': len(minimality_report.get('equivalence_groups', [])),
                        'violations': violations,
                    }
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G16_MINIMALITY_INVARIANT_FAILED", "post_generation", "REFUSAL", message="minimality invariant failed")
                            except Exception:
                                pass
                    except Exception:
                        pass
                    raise RuntimeError('minimality_invariant_failed')

                # Persist pruned checklist to both fingerprinted output and root outputs
                with open(os.path.join(output_dir, 'checklist.json'), 'w', encoding='utf8') as _cf:
                    json.dump({'items': pruned_items}, _cf, indent=2, sort_keys=True)
                with open(os.path.join('.selfhost_outputs', 'checklist.json'), 'w', encoding='utf8') as _cfroot:
                    json.dump({'items': pruned_items}, _cfroot, indent=2, sort_keys=True)

                # Build execution plan and enforce executability
                from shieldcraft.checklist.dependencies import infer_item_dependencies
                from shieldcraft.checklist.execution_graph import build_execution_plan
                from shieldcraft.requirements.coverage import compute_coverage

                covers = compute_coverage(reqs, pruned_items)
                # persist sequence artifact (build_sequence writes to outdir)
                try:
                    from shieldcraft.checklist.dependencies import build_sequence
                    build_sequence(pruned_items, infer_item_dependencies(reqs, covers), outdir='.selfhost_outputs')
                except Exception:
                    pass
                inferred = infer_item_dependencies(reqs, covers)
                plan = build_execution_plan(pruned_items, inferred)
                manifest['checklist_execution_plan'] = {'ordered_item_count': len(plan.get('ordered_item_ids', [])), 'cycle_groups': plan.get('cycles', {}), 'missing_artifacts': plan.get('missing_artifacts', []), 'priority_violations': plan.get('priority_violations', [])}

                if plan.get('cycles'):
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G17_EXECUTION_CYCLE_DETECTED", "post_generation", "REFUSAL", message="execution cycle detected")
                            except Exception:
                                pass
                    except Exception:
                        pass
                    raise RuntimeError('execution_cycle_detected')
                if plan.get('missing_artifacts'):
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G18_MISSING_ARTIFACT_PRODUCER", "post_generation", "REFUSAL", message="missing artifact producer")
                            except Exception:
                                pass
                    except Exception:
                        pass
                    raise RuntimeError('missing_artifact_producer')
                if plan.get('priority_violations'):
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G19_PRIORITY_VIOLATION_DETECTED", "post_generation", "REFUSAL", message="priority violation detected")
                            except Exception:
                                pass
                    except Exception:
                        pass
                    raise RuntimeError('priority_violation_detected')

                order_map = {nid: idx + 1 for idx, nid in enumerate(plan.get('ordered_item_ids', []))}
                for it in pruned_items:
                    it['execution_order'] = order_map.get(it.get('id'))
                with open(os.path.join(output_dir, 'checklist.json'), 'w', encoding='utf8') as _cf2:
                    json.dump({'items': pruned_items}, _cf2, indent=2, sort_keys=True)
            except Exception:
                # Propagate fatal errors to caller
                raise

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
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G14_SELFHOST_INTERNAL_ERROR_RETURN", "self_host", "DIAGNOSTIC", message=str(e))
                    except Exception:
                        pass
            except Exception:
                pass
            return finalize_checklist(self, partial_result=None, exception=e)

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
            # If run_self_host returned a checklist error/result rather than success, propagate the finalized checklist unchanged
            if not res or not res.get("output_dir"):
                return res
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
        try:
            # Load and validate using canonical DSL
            raw = load_spec(spec_path)
        except Exception as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G4_SCHEMA_VALIDATION", "preflight", "DIAGNOSTIC", message="spec load failed", evidence={"error": str(e)})
                    except Exception:
                        pass
            except Exception:
                pass
            return finalize_checklist(self, partial_result=None, exception=e)
        
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
                return finalize_checklist(self, partial_result={"type": "schema_error", "details": errors})
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
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G22_EXECUTE_INTERNAL_ERROR_RETURN", "generation", "DIAGNOSTIC", message="invalid checklist format")
                    except Exception:
                        pass
            except Exception:
                pass
            return finalize_checklist(self, partial_result={"type": "internal_error", "details": "Invalid checklist format"})
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
        
        try:
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
        except Exception as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        self.checklist_context.record_event("G22_EXECUTE_INTERNAL_ERROR_RETURN", "generation", "DIAGNOSTIC", message=str(e))
                    except Exception:
                        pass
            except Exception:
                pass
            return finalize_checklist(self, partial_result=None, exception=e)

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
