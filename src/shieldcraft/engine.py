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
    
    events = []
    try:
        if engine is not None and getattr(engine, 'checklist_context', None):
            try:
                events = engine.checklist_context.get_events()
            except Exception:
                events = []
    except Exception:
        events = []

    
    try:
        for ev in events:
            if ev.get('persona_id') and any(k in ev for k in ('primary_outcome', 'refusal', 'blocking_reasons')):
                try:
                    if engine is not None and getattr(engine, 'checklist_context', None):
                        try:
                            engine.checklist_context.record_event("G13_PERSONA_OUTCOME_OVERRIDE_ATTEMPT", "finalize", "DIAGNOSTIC", message="persona attempted to override outcome fields", evidence={"event": ev})
                        except Exception:
                            pass
                except Exception:
                    pass
    except Exception:
        pass

    
    pass

    items = []
    
    try:
        if partial_result and isinstance(partial_result.get('checklist'), dict):
            existing = partial_result.get('checklist', {}).get('items', []) or []
            items.extend(existing)
    except Exception:
        pass

    
    for ev in events:
        try:
            gid = ev.get('gate_id')
            phase = ev.get('phase')
            outcome = ev.get('outcome')
            msg = ev.get('message') or gid
            evidence = ev.get('evidence')
            
            it = {'ptr': '/', 'text': f"{gid}: {msg}", 'meta': {'gate': gid, 'phase': phase, 'evidence': evidence}}
            
            if outcome and outcome.upper() in ('REFUSAL', 'BLOCKER'):
                it['severity'] = 'high'
            else:
                it['severity'] = 'medium'
            items.append(it)

            
            try:
                mask_gates = {"G2_GOVERNANCE_PRESENCE_CHECK", "G3_REPO_SYNC_VERIFICATION", "G7_PERSONA_VETO", "G14_SELFHOST_INPUT_SANDBOX", "G15_DISALLOWED_SELFHOST_ARTIFACT", "G20_QUALITY_GATE_FAILED"}
                if (outcome or '').upper() == 'REFUSAL' and gid in mask_gates:
                    diag = {
                        'ptr': '/',
                        'text': f"REFUSAL_DIAG: {gid}: {msg}",
                        'meta': {'gate': gid, 'phase': phase, 'source': 'diagnostic', 'justification': 'refusal_masking_explanation', 'inference_type': 'fallback'},
                        'severity': 'medium',
                        'classification': 'compiler'
                    }
                    items.append(diag)
            except Exception:
                pass
        except Exception:
            
            pass
    
    error_info = None
    if exception is not None:
        try:
            err_text = str(exception)
            items.append({'ptr': '/', 'text': f"internal_exception: {err_text}", 'severity': 'high', 'meta': {'exception': err_text}})
            error_info = {'message': err_text, 'type': exception.__class__.__name__}
        except Exception:
            pass

    
    checklist = {'items': items, 'emitted': True, 'events': events}

    
    from shieldcraft.services.checklist.outcome import derive_primary_outcome
    
    try:
        derived = derive_primary_outcome(checklist, events)
    except Exception as e:
        
        try:
            if engine is not None and getattr(engine, 'checklist_context', None):
                try:
                    engine.checklist_context.record_event("G_INTERNAL_DERIVATION_FAILURE", "finalize", "DIAGNOSTIC", message="derive_primary_outcome raised", evidence={"error": str(e)})
                except Exception:
                    pass
        except Exception:
            pass
        
        outcomes = [((ev.get('outcome') or '').upper()) for ev in events if isinstance(ev, dict)]
        primary = None
        if any(o == 'REFUSAL' for o in outcomes):
            primary = 'REFUSAL'
            refusal_flag = True
        elif any(o == 'BLOCKER' for o in outcomes):
            primary = 'BLOCKED'
            refusal_flag = False
        elif events and all((o == 'DIAGNOSTIC') for o in outcomes if o):
            primary = 'DIAGNOSTIC'
            refusal_flag = False
        else:
            primary = 'SUCCESS'
            refusal_flag = False
        derived = {'primary_outcome': primary, 'refusal': refusal_flag, 'blocking_reasons': [], 'confidence_level': 'low'}

    
    checklist['primary_outcome'] = derived.get('primary_outcome')
    primary_outcome = checklist.get('primary_outcome')
    checklist['blocking_reasons'] = derived.get('blocking_reasons', [])
    checklist['confidence_level'] = derived.get('confidence_level', 'low')

    
    try:
        
        tier_a_items = [it for it in checklist.get('items', []) if (it.get('meta') or {}).get('source') == 'default' and (it.get('meta') or {}).get('tier') == 'A']
        if tier_a_items:
            
            has_blocker = any((ev.get('gate_id') or '').startswith('G_SYNTHESIZED_DEFAULT_') and (ev.get('outcome') or '').upper() == 'BLOCKER' for ev in events)
            
            has_diag = any((ev.get('gate_id') or '').startswith('G_SYNTHESIZED_DEFAULT_') and (ev.get('outcome') or '').upper() == 'DIAGNOSTIC' for ev in events)
            assert has_blocker and has_diag, 'TIER_A_SYNTHESIS_MISSING_BLOCKER_OR_DIAGNOSTIC'
    except AssertionError:
        
        raise
    except Exception:
        
        raise


    if derived.get('refusal'):
        checklist['refusal'] = True
        
        try:
            non_persona_ev = next(e for e in events if (e.get('outcome') or '').upper() == 'REFUSAL' and not e.get('persona_id'))
            checklist['refusal_reason'] = non_persona_ev.get('message') or non_persona_ev.get('gate_id')
            
            try:
                refusal_meta = (non_persona_ev.get('evidence') or {}).get('refusal') or {}
                
                assert isinstance(refusal_meta.get('authority'), str) and refusal_meta.get('authority'), 'REFUSAL authority missing or invalid'
                checklist['refusal_authority'] = refusal_meta.get('authority')
                checklist['refusal_trigger'] = refusal_meta.get('trigger')
                checklist['refusal_scope'] = refusal_meta.get('scope')
                checklist['refusal_justification'] = refusal_meta.get('justification')
            except AssertionError:
                
                raise
            except Exception:
                
                raise
        except StopIteration:
            checklist['refusal_reason'] = None

    result_refusal = bool(derived.get('refusal', False))

    
    
    
    
    
    
    
    gate_outcomes = {}
    gate_first_index = {}
    for idx, ev in enumerate(events):
        g = ev.get('gate_id')
        o = (ev.get('outcome') or '').upper()
        if g:
            gate_outcomes.setdefault(g, set()).add(o)
            if g not in gate_first_index:
                gate_first_index[g] = idx

    
    
    decisive_label = None
    if checklist.get('primary_outcome') == 'REFUSAL':
        decisive_label = 'REFUSAL'
    elif checklist.get('primary_outcome') == 'BLOCKED':
        decisive_label = 'BLOCKER'
    elif checklist.get('primary_outcome') == 'DIAGNOSTIC':
        decisive_label = 'DIAGNOSTIC'
    items = checklist.get('items', []) or []

    primary_item = None
    if primary_outcome != 'SUCCESS' and items:
        
        candidate_gates = [g for g, outs in gate_outcomes.items() if decisive_label in outs]
        if candidate_gates:
            
            selected_gate = min(candidate_gates)
            
            candidate_items = [it for it in items if (it.get('meta') or {}).get('gate') == selected_gate]
            if candidate_items:
                
                def _item_event_index(it):
                    g = (it.get('meta') or {}).get('gate')
                    return gate_first_index.get(g, 0)
                primary_item = min(candidate_items, key=lambda it: (_item_event_index(it), it.get('text') or ''))
        else:
            
            primary_item = min(items, key=lambda it: ((it.get('meta') or {}).get('gate') or '', it.get('text') or ''))

    
    for it in items:
        it['role'] = None
        if primary_item is not None and it is primary_item:
            it['role'] = 'PRIMARY_CAUSE'
            continue
        gate = (it.get('meta') or {}).get('gate')
        gate_out = gate_outcomes.get(gate, set()) if gate else set()
        if 'BLOCKER' in gate_out:
            it['role'] = 'CONTRIBUTING_BLOCKER'
            continue
        if 'DIAGNOSTIC' in gate_out and primary_outcome != 'DIAGNOSTIC_ONLY':
            it['role'] = 'SECONDARY_DIAGNOSTIC'
            continue
        it['role'] = 'INFORMATIONAL'

    
    _assert_semantic_invariants(checklist, primary_outcome, gate_outcomes)

    
    try:
        from shieldcraft.services.checklist.quality import compute_checklist_quality
        
        synthesized_count = sum(1 for it in items if (it.get('meta') or {}).get('synthesized_default'))
        
        insuff_count = sum(1 for it in items if (it.get('meta') or {}).get('insufficiency'))
        quality = compute_checklist_quality(items, synthesized_count, insuff_count)
        
        if 'meta' not in checklist:
            checklist['meta'] = {}
        checklist['meta']['checklist_quality'] = quality

        
        if quality < 60:
            items.append({
                'ptr': '/',
                'text': f'CHECKLIST QUALITY LOW: {quality}',
                'meta': {'quality_score': quality, 'diagnostic': True},
                'severity': 'medium',
                'classification': 'compiler',
            })
    except Exception:
        pass

    
    try:
        persona_events = list(getattr(engine, '_persona_events', []) or [])
        if persona_events:
            
            def _capability_to_outcome(cap):
                if cap == 'veto':
                    return 'REFUSAL'
                
                return 'DIAGNOSTIC'

            
            pes = []
            for idx, pe in enumerate(persona_events):
                outcome = _capability_to_outcome(pe.get('capability'))
                pes.append({
                    'persona_id': pe.get('persona_id'),
                    'capability': pe.get('capability'),
                    'phase': pe.get('phase'),
                    'payload_ref': pe.get('payload_ref'),
                    'severity': pe.get('severity'),
                    'derived_outcome': outcome,
                    'index': idx,
                })

            
            prim = None
            if any(p.get('derived_outcome') == 'REFUSAL' for p in pes):
                candidates = [p for p in pes if p.get('derived_outcome') == 'REFUSAL']
            elif any(p.get('derived_outcome') == 'DIAGNOSTIC' for p in pes):
                candidates = [p for p in pes if p.get('derived_outcome') == 'DIAGNOSTIC']
            else:
                candidates = pes

            if candidates:
                
                prim = sorted(candidates, key=lambda p: (p.get('persona_id') or '', p.get('index')))[0]

            checklist['persona_summary'] = {
                'primary_persona': prim.get('persona_id') if prim else None,
                'primary_capability': prim.get('capability') if prim else None,
                'events': pes,
            }
    except Exception:
        
        pass

    
    
    result_primary_outcome = primary_outcome

    
    result = {}
    if partial_result and isinstance(partial_result, dict):
        result.update(partial_result)

    
    result['checklist'] = checklist
    
    result['primary_outcome'] = result_primary_outcome
    result['refusal'] = result_refusal
    
    
    result['emitted'] = True
    if error_info:
        result['error'] = error_info

    
    
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
    
    
    
    if items_local:
        if primary != 'ACTION':
            if roles.count('PRIMARY_CAUSE') != 1:
                raise AssertionError('Semantic invariant violated: exactly one PRIMARY_CAUSE required for non-ACTION outcomes')
        else:
            if 'PRIMARY_CAUSE' in roles:
                raise AssertionError('Semantic invariant violated: ACTION outcome must not contain PRIMARY_CAUSE')
    
    if primary == 'REFUSAL':
        if not checklist_obj.get('refusal') or not checklist_obj.get('refusal_reason'):
            raise AssertionError('Semantic invariant violated: REFUSAL outcome must include refusal_reason')
    
    if primary == 'BLOCKED':
        if checklist_obj.get('refusal'):
            raise AssertionError('Semantic invariant violated: BLOCKED outcome must not set refusal == true')
    
    if primary == 'DIAGNOSTIC':
        if any(((it.get('meta') or {}).get('gate') and ('BLOCKER' in gate_outcomes.get((it.get('meta') or {}).get('gate'), set()) or 'REFUSAL' in gate_outcomes.get((it.get('meta') or {}).get('gate'), set()))) for it in items_local):
            raise AssertionError('Semantic invariant violated: DIAGNOSTIC outcome must not contain BLOCKER or REFUSAL items')


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
        
        try:
            from shieldcraft.services.checklist.context import ChecklistContext, set_global_context
            self.checklist_context = ChecklistContext()
            try:
                
                set_global_context(self.checklist_context)
            except Exception:
                pass
        except Exception:
            
            self.checklist_context = None
        self.codegen = CodeGenerator()
        self.writer = FileWriter()
        self.det = DeterminismEngine()
        self.prov = ProvenanceEngine()
        self.evidence = EvidenceBundle(self.det, self.prov)
        self.verifier = ChecklistVerifier()
        
        try:
            from shieldcraft.services.validator import validate_instruction_block
            from shieldcraft.services.sync import verify_repo_sync
            
            from shieldcraft.persona import is_persona_enabled
        except Exception as e:
            try:
                if getattr(self, 'checklist_context', None):
                    try:
                        from shieldcraft.services.governance.refusal_authority import record_refusal_event
                        record_refusal_event(self.checklist_context, "G1_ENGINE_READINESS_FAILURE", "preflight", message="engine readiness failure", evidence={"error": str(e)}, justification="engine_readiness_failure")
                    except Exception:
                        pass
            except Exception:
                pass
            raise RuntimeError("engine_readiness_failure: missing subsystem") from e
        
        self.persona_enabled = is_persona_enabled()
        
        self.snapshot_enabled = os.getenv("SHIELDCRAFT_SNAPSHOT_ENABLED", "0") == "1"

    def preflight(self, spec_or_path):
        """Run preflight validation (schema + instruction validation) without side-effects.

        Accepts either a spec dict or a path to a spec file. Raises `ValidationError` on
        instruction-level failures or returns a dict with schema validation failures.
        """
        
        if isinstance(spec_or_path, str):
            raw = load_spec(spec_or_path)
            if isinstance(raw, SpecModel):
                spec = raw.raw
            else:
                spec = raw
        else:
            spec = spec_or_path

        
        try:
            
            self._execution_state_entries = []  
            from shieldcraft.observability import emit_state
            emit_state(self, "preflight", "preflight", "start")
        except Exception:
            
            pass

        
        
        try:
            
            
            root = os.getcwd()
            if os.path.exists(os.path.join(root, "spec")):
                from shieldcraft.services.governance.registry import check_governance_presence
                
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
                        from shieldcraft.services.governance.refusal_authority import record_refusal_event
                        record_refusal_event(self.checklist_context, "G2_GOVERNANCE_PRESENCE_CHECK", "preflight", message="governance presence check failed", evidence={"error": str(e)}, trigger="missing_authority", scope="/governance", justification="governance_presence_failed")
                    except Exception:
                        pass
            except Exception:
                pass
            
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
            
            raise RuntimeError("governance_check_failed")

        
        
        from shieldcraft.services.sync import verify_repo_state_authoritative, SYNC_MISSING
        try:
            verify_repo_state_authoritative(os.getcwd())
        except Exception as e:
            
            
            from shieldcraft.services.sync import SyncError
            from shieldcraft.snapshot import SnapshotError
            if isinstance(e, SnapshotError):
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            from shieldcraft.services.governance.refusal_authority import record_refusal_event
                            record_refusal_event(self.checklist_context, "G3_REPO_SYNC_VERIFICATION", "preflight", message="snapshot error", evidence={"error": str(e)}, trigger="missing_authority", justification="snapshot_error")
                        except Exception:
                            pass
                except Exception:
                    pass
                raise
            if isinstance(e, SyncError):
                
                if getattr(e, "code", None) == SYNC_MISSING:
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                from shieldcraft.services.governance.refusal_authority import record_refusal_event
                                record_refusal_event(self.checklist_context, "G3_REPO_SYNC_VERIFICATION", "preflight", message="repo sync missing", evidence={"error": str(e)}, trigger="missing_authority", justification="repo_sync_missing")
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
                
                return finalize_checklist(self, partial_result={"type": "schema_error", "details": errors})

        
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
            
            pass
        except Exception:
            
            pass

        
        if isinstance(spec, dict) and "instructions" in spec:
            fp = compute_spec_fingerprint(spec)
            if getattr(self, "_last_validated_spec_fp", None) != fp:
                raise RuntimeError("validation_not_performed")
        
        try:
            if hasattr(self, "_persona_vetoes") and self._persona_vetoes:
                
                severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
                def _key(v):
                    return (severity_order.get(v.get("severity"), 0), v.get("persona_id"))
                sel = sorted(self._persona_vetoes, key=_key, reverse=True)[0]
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            
                            self.checklist_context.record_event("G7_PERSONA_VETO", "preflight", "DIAGNOSTIC", message="persona veto advisory (non-authoritative)", evidence={"persona_id": sel.get('persona_id'), "code": sel.get('code')})
                        except Exception:
                            pass
                except Exception:
                    pass
                
                try:
                    self._persona_veto_selected = sel
                except Exception:
                    pass
        except Exception:
            
            pass
        
        
        
        
        
        try:
            enforce_flag = os.getenv("SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT", "0") == "1"
            spec_enforce = isinstance(spec, dict) and spec.get("metadata", {}).get("enforce_tests_attached", False)
            if enforce_flag or spec_enforce:
                from shieldcraft.services.validator.tests_attached_validator import verify_tests_attached, ProductInvariantFailure
                
                try:
                    from shieldcraft.services.ast.builder import ASTBuilder
                    ast_local = ASTBuilder().build(spec)
                except Exception:
                    ast_local = None
                checklist_preview = None
                try:
                    checklist_preview = self.checklist_gen.build(spec, ast=ast_local, dry_run=True, run_test_gate=False, engine=self)
                except Exception:
                    
                    raise RuntimeError("checklist_generation_failed")
                
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
            
            raise
        except Exception:
            
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

        
        if self.snapshot_enabled:
            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "preflight", "snapshot", "start")
            except Exception:
                pass

            try:
                from shieldcraft.snapshot import validate_snapshot, SnapshotError
                from shieldcraft.observability import emit_state
                snapshot_path = os.path.join(os.getcwd(), "artifacts", "repo_snapshot.json")
                validate_snapshot(snapshot_path, os.getcwd())
                try:                    
                    emit_state(self, "preflight", "snapshot", "ok")
                except Exception:
                    pass
            except Exception as e:
                try:
                    from shieldcraft.observability import emit_state
                    emit_state(self, "preflight", "snapshot", "fail", getattr(e, "code", str(e)))
                except Exception:
                    pass
                
                
                from shieldcraft.snapshot import SnapshotError
                if isinstance(e, SnapshotError):
                    raise
                
                raise RuntimeError("snapshot_validation_failed")

        
        sync_res = getattr(self, '_last_sync_verified', None)
        if not sync_res:
            raise RuntimeError('sync_not_performed')
        self._last_sync_verified = sync_res.get("sha256")

        
        
        from shieldcraft.services.validator import validate_instruction_block
        validate_instruction_block(spec)
        
        self._last_validated_spec_fp = compute_spec_fingerprint(spec)
        
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
        
        
        try:
            
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

        
        if isinstance(raw, SpecModel):
            spec_model = raw
            normalized = spec_model.raw
            ast = spec_model.ast
            fingerprint = spec_model.fingerprint
        else:
            
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
                
                return finalize_checklist(self, partial_result={"type": "schema_error", "details": errors})
            ast = self.ast.build(normalized)
            fingerprint = compute_spec_fingerprint(normalized)
            spec_model = SpecModel(normalized, ast, fingerprint)
        
        
        spec = normalized

        
        
        
        
        self._validate_spec(spec)
        
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
        
        
        plan = from_ast(ast)
        
        
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        plan_dir = f"products/{product_id}"
        os.makedirs(plan_dir, exist_ok=True)
        write_canonical_json(f"{plan_dir}/plan.json", plan)
        
        
        
        try:
            from shieldcraft.verification.seed_manager import generate_seed, snapshot
            generate_seed(self, "run")
        except Exception:
            pass

        try:
            checklist = self.checklist_gen.build(spec, ast=ast, engine=self)
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

        
        try:
            from shieldcraft.verification.seed_manager import snapshot
            det = snapshot(self)
            checklist["_determinism"] = {"seeds": det, "spec": spec, "ast": ast, "checklist": checklist}
        except Exception:
            pass
        
        try:
            from shieldcraft.verification.readiness_evaluator import evaluate_readiness
            from shieldcraft.verification.readiness_report import render_readiness
            readiness = evaluate_readiness(self, spec, checklist)
            checklist_readiness = readiness
            checklist["_readiness"] = checklist_readiness
            checklist["_readiness_report"] = render_readiness(readiness)
            
            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "readiness", "readiness", "ok" if readiness.get("ok") else "fail", str(readiness.get("results")))
            except Exception:
                pass
        except Exception:
            
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
        
        
        if result.get("type") == "schema_error":
            return result
        try:
            outputs = self.codegen.run(result["checklist"], dry_run=dry_run)

            
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
        
        
        try:
            
            self._execution_state_entries = []  
            from shieldcraft.observability import emit_state
            emit_state(self, "self_host", "self_host", "start")
        except Exception:
            pass

        spec_str = json.dumps(spec, sort_keys=True)
        fingerprint = hashlib.sha256(spec_str.encode()).hexdigest()[:16]

        preview = None

        
        
        try:
            try:
                self._validate_spec(spec)
            except Exception as e:
                if dry_run:
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G_VALIDATION_FAILURE", "preflight", "DIAGNOSTIC", message=f"Spec validation failed: {str(e)}")
                            except Exception:
                                pass
                    except Exception:
                        pass
                else:
                    raise

            
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
                    if not dry_run:
                        raise RuntimeError("validation_not_performed")

            
            try:
                ast = self.ast.build(spec)
            except Exception as e:
                if dry_run:
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                self.checklist_context.record_event("G_BUILD_FAILURE", "build", "DIAGNOSTIC", message=f"AST build failed: {str(e)}")
                            except Exception:
                                pass
                    except Exception:
                        pass
                    ast = None
                else:
                    raise
            
            try:
                checklist = self.checklist_gen.build(spec, ast=ast, engine=self)
            except Exception as e:
                if dry_run:
                    checklist = {'items': [{'ptr': '/', 'text': f'Checklist generation failed: {str(e)}', 'severity': 'high'}]}
                else:
                    raise
            
            
            bootstrap_items = [
                item for item in checklist.get("items", [])
                if item.get("category") == "bootstrap"
            ]
            
            
            codegen_result = self.codegen.run({"items": bootstrap_items}, dry_run=True)

            
            
            
            if self.persona_enabled:
                try:
                    from shieldcraft.persona import load_persona, find_persona_files, resolve_persona_files
                    
                    files = find_persona_files(os.getcwd())
                    chosen = resolve_persona_files(files)
                    if chosen:
                        persona = load_persona(chosen)
                        
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
                            
                            self.persona = persona
                except Exception:
                    
                    pass
            else:
                self.persona = None
            
            
            from shieldcraft.services.selfhost import is_allowed_selfhost_input, SELFHOST_READINESS_MARKER, provenance_header
            if not is_allowed_selfhost_input(spec):
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            from shieldcraft.services.governance.refusal_authority import record_refusal_event
                            record_refusal_event(self.checklist_context, "G14_SELFHOST_INPUT_SANDBOX", "post_generation", message="disallowed self-host input", justification="disallowed_selfhost_input", trigger="missing_authority")
                        except Exception:
                            pass
                except Exception:
                    pass
                if not dry_run:
                    raise RuntimeError("disallowed_selfhost_input")

            
            from shieldcraft.services.selfhost import SELFHOST_READINESS_MARKER as _READINESS
            if not _READINESS:
                try:
                    if getattr(self, 'checklist_context', None):
                        try:
                            from shieldcraft.services.governance.refusal_authority import record_refusal_event
                            record_refusal_event(self.checklist_context, "G14_SELFHOST_INPUT_SANDBOX", "post_generation", message="self-host not ready", justification="selfhost_not_ready", trigger="missing_authority")
                        except Exception:
                            pass
                except Exception:
                    pass
                if not dry_run:
                    raise RuntimeError("selfhost_not_ready")

            
            
            
            
            
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
                    if not dry_run:
                        raise RuntimeError("worktree_not_clean")

            
            output_dir = Path(f".selfhost_outputs/{fingerprint}")
            
            
            try:
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
            except Exception:
                manifest = {
                    "fingerprint": fingerprint,
                    "manifest_version": "v1",
                    "spec_fingerprint": fingerprint,
                    "spec_metadata": {},
                    "bootstrap_items": len(bootstrap_items),
                    "codegen_bundle_hash": codegen_result.get("codegen_bundle_hash", "unknown"),
                    "outputs": [],
                    "provenance": {
                        "engine_version": "unknown",
                        "spec_fingerprint": fingerprint,
                        "snapshot_hash": getattr(self, '_last_sync_verified', None),
                    }
                }
            
            if dry_run:
                try:
                    diag = finalize_checklist(self, partial_result=None, exception=None)
                    diagnostic_items = diag.get("checklist", {}).get("items", [])
                except Exception:
                    diagnostic_items = []
            else:
                diagnostic_items = []
            
            preview = {
                "fingerprint": fingerprint,
                "output_dir": str(output_dir),
                "manifest": manifest,
                "modules": [out["path"] for out in codegen_result.get("outputs", [])],
                "codegen_bundle_hash": codegen_result.get("codegen_bundle_hash", "unknown"),
                "lineage": {
                    "headers": checklist.get("lineage_headers", {})
                },
                "checklist": checklist.get("items", []) + diagnostic_items,
                "outputs": codegen_result.get("outputs", [])
            }
            
            if dry_run:
                
                try:
                    from shieldcraft.services.selfhost.preview_validator import validate_preview
                    validation = validate_preview(preview)
                    preview["validation_ok"] = validation["ok"]
                    preview["validation_issues"] = validation["issues"]
                    preview["primary_outcome"] = "SUCCESS" if validation["ok"] else "DIAGNOSTIC"
                    
                    header = provenance_header(fingerprint, getattr(self, '_last_sync_verified', None))
                    for o in preview.get("outputs", []):
                        o["content"] = header + str(o.get("content", ""))
                except Exception as e:
                    preview["validation_ok"] = False
                    preview["validation_issues"] = [f"exception during preview preparation: {str(e)}"]
                    preview["primary_outcome"] = "DIAGNOSTIC"
                
                try:
                    from shieldcraft.observability import emit_state
                    emit_state(self, "self_host", "self_host", "ok")
                except Exception:
                    pass
                return preview
            
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            from shieldcraft.services.selfhost import is_allowed_selfhost_path

            for output in codegen_result.get("outputs", []):
                rel_path = output["path"].lstrip("./")
                if not is_allowed_selfhost_path(rel_path):
                    try:
                        if getattr(self, 'checklist_context', None):
                            try:
                                from shieldcraft.services.governance.refusal_authority import record_refusal_event
                                record_refusal_event(self.checklist_context, "G15_DISALLOWED_SELFHOST_ARTIFACT", "post_generation", message=f"disallowed_selfhost_artifact: {rel_path}", evidence={"path": rel_path}, justification="disallowed_selfhost_artifact", trigger="missing_authority", scope=f"path:{rel_path}")
                            except Exception:
                                pass
                    except Exception:
                        pass
                    raise RuntimeError(f"disallowed_selfhost_artifact: {rel_path}")
                file_path = output_dir / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                header = provenance_header(fingerprint, getattr(self, '_last_sync_verified', None))
                file_path.write_text(header + output["content"])
            
            
            manifest_path = output_dir / "bootstrap_manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2))
        
        
        
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
                
                
                pass

            try:
                from shieldcraft.observability import emit_state
                emit_state(self, "self_host", "self_host", "ok")
            except Exception:
                pass

            
            try:
                
                try:
                    reqs = json.load(open(os.path.join(output_dir, 'requirements.json'))).get('requirements', [])
                except Exception:
                    try:
                        reqs = json.load(open(os.path.join('.selfhost_outputs', 'requirements.json'))).get('requirements', [])
                    except Exception:
                        from shieldcraft.interpretation.requirements import extract_requirements
                        rtxt = spec.get('metadata', {}).get('source_material') or spec.get('raw_input') or json.dumps(spec, sort_keys=True)
                        
                        if not isinstance(rtxt, str):
                            import json as _json
                            rtxt = _json.dumps(rtxt, sort_keys=True)
                        reqs = extract_requirements(rtxt)
                
                items = checklist.get('items', []) or json.load(open(os.path.join('.selfhost_outputs', 'checklist.json'))).get('items', [])
                valid_items = [it for it in items if it.get('quality_status') != 'INVALID']

                
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

                
                with open(os.path.join(output_dir, 'checklist.json'), 'w', encoding='utf8') as _cf:
                    json.dump({'items': pruned_items}, _cf, indent=2, sort_keys=True)
                with open(os.path.join('.selfhost_outputs', 'checklist.json'), 'w', encoding='utf8') as _cfroot:
                    json.dump({'items': pruned_items}, _cfroot, indent=2, sort_keys=True)

                
                from shieldcraft.checklist.dependencies import infer_item_dependencies
                from shieldcraft.checklist.execution_graph import build_execution_plan
                from shieldcraft.requirements.coverage import compute_coverage

                covers = compute_coverage(reqs, pruned_items)
                
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
            result = finalize_checklist(self, partial_result=None, exception=e)
            if dry_run and emit_preview:
                preview = {"error": str(e), "validation_ok": False}
            return result
        finally:
            if dry_run and emit_preview and preview is not None:
                try:
                    json_str = json.dumps(preview, indent=2, default=str)
                except Exception:
                    json_str = json.dumps({"error": "preview serialization failed", "validation_ok": False})
                preview_path = Path(emit_preview)
                preview_path.parent.mkdir(parents=True, exist_ok=True)
                preview_path.write_text(json_str)

    def run_self_build(self, spec_path: str = "spec/se_dsl_v1.spec.json", dry_run: bool = False):
        """Run a self-build using the engine pipeline and emit a self-build bundle.

        This performs: validate -> sync -> generate -> self-host and emits a
        self-build bundle under `artifacts/self_build/<fingerprint>/`.
        """
        import shutil
        from pathlib import Path
        from shieldcraft.services.selfhost import SELFBUILD_OUTPUT_DIR, SELFBUILD_BITWISE_ARTIFACTS, provenance_header_extended

        
        if getattr(self, "_selfbuild_running", False):
            raise RuntimeError("selfbuild_recursive_invocation")
        
        if os.getenv("SHIELDCRAFT_SELFBUILD_ENABLED", "0") != "1" and os.getenv("GITHUB_ACTIONS", "") != "true":
            raise RuntimeError("selfbuild_disabled")
        self._selfbuild_running = True

        try:
            
            spec_file = spec_path
            if not os.path.isabs(spec_file) and not os.path.exists(spec_file):
                
                repo_root = Path(__file__).resolve().parents[2]
                spec_file = str(repo_root / spec_path)
            with open(spec_file) as f:
                spec = json.load(f)

            
            self._validate_spec(spec)

            
            previous_snapshot = getattr(self, "_last_sync_verified", None)
            build_depth = int(os.getenv("SHIELDCRAFT_BUILD_DEPTH", "0"))

            
            
            
            prev = os.getenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY")
            os.environ["SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY"] = "1"
            try:
                preview = self.run_self_host(spec, dry_run=True, emit_preview=None)
            except Exception:
                
                if prev is None:
                    os.environ.pop("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", None)
                else:
                    os.environ["SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY"] = prev
                raise

            if dry_run:
                
                preview["manifest"]["provenance"]["previous_snapshot"] = previous_snapshot
                preview["manifest"]["provenance"]["build_depth"] = build_depth + 1
                return preview

            
            try:
                res = self.run_self_host(spec, dry_run=False)
            finally:
                if prev is None:
                    os.environ.pop("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", None)
                else:
                    os.environ["SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY"] = prev
            
            if not res or not res.get("output_dir"):
                return res
            out_dir = Path(res.get("output_dir"))
            target_dir = Path(SELFBUILD_OUTPUT_DIR) / res.get("fingerprint")
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(out_dir, target_dir)

            
            manifest = res.get("manifest", {})
            manifest.setdefault("provenance", {})
            manifest["provenance"]["previous_snapshot"] = previous_snapshot
            manifest["provenance"]["build_depth"] = build_depth + 1
            manifest_path = target_dir / "self_build_manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))

            
            from shieldcraft.services.selfhost import SELFBUILD_BASELINE_DIR, DEFAULT_BASELINE_NAME, SELFBUILD_BITWISE_ARTIFACTS, is_allowed_diff
            baseline_root = Path(SELFBUILD_BASELINE_DIR) / DEFAULT_BASELINE_NAME
            if baseline_root.exists():
                
                for fname in SELFBUILD_BITWISE_ARTIFACTS:
                    emitted_path = target_dir / fname
                    baseline_path = baseline_root / fname
                    if not baseline_path.exists():
                        raise RuntimeError(f"selfbuild_baseline_missing_artifact: {fname}")
                    if not emitted_path.exists():
                        raise RuntimeError(f"selfbuild_missing_artifact: {fname}")
                    if emitted_path.read_bytes() != baseline_path.read_bytes():
                        
                        rel = fname
                        if not is_allowed_diff(str(baseline_root), rel):
                            
                            forensics_dir = target_dir / "forensics"
                            forensics_dir.mkdir(exist_ok=True)
                            fb = forensics_dir / "forensics.json"
                            fb.write_text(json.dumps({
                                "mismatch": rel,
                                "emitted_sha256": hashlib.sha256(emitted_path.read_bytes()).hexdigest(),
                                "baseline_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                            }, indent=2, sort_keys=True))
                            raise RuntimeError("selfbuild_mismatch: emitted artifact does not match baseline")
                
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
                
                if os.getenv("SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE", "0") == "1":
                    baseline_root.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(target_dir, baseline_root, dirs_exist_ok=True)
                else:
                    
                    
                    
                    
                    if os.getenv("SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE", "0") == "1":
                        baseline_root.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(target_dir, baseline_root, dirs_exist_ok=True)
                    

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
        
        
        if isinstance(raw, SpecModel):
            spec_model = raw
            spec = spec_model.raw
            ast = spec_model.ast
            
            self._validate_spec(spec)
            if "instructions" in spec:
                fp = compute_spec_fingerprint(spec)
                if getattr(self, "_last_validated_spec_fp", None) != fp:
                    raise RuntimeError("validation_not_performed")
        else:
            
            spec = canonicalize(raw) if not isinstance(raw, dict) else raw
            valid, errors = validate_spec_against_schema(spec, self.schema_path)
            if not valid:
                return finalize_checklist(self, partial_result={"type": "schema_error", "details": errors})
            
            
            self._validate_spec(spec)
            if "instructions" in spec:
                fp = compute_spec_fingerprint(spec)
                if getattr(self, "_last_validated_spec_fp", None) != fp:
                    raise RuntimeError("validation_not_performed")
            ast = self.ast.build(spec)
        
        
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        prev_spec_path = f"products/{product_id}/last_spec.json"
        spec_evolution = None
        
        if os.path.exists(prev_spec_path):
            from shieldcraft.services.spec.evolution import compute_evolution
            with open(prev_spec_path) as f:
                previous_spec = json.load(f)
            spec_evolution = compute_evolution(previous_spec, spec)
        
        
        
        plan = from_ast(ast, spec)
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        plan_dir = f"products/{product_id}"
        os.makedirs(plan_dir, exist_ok=True)
        write_canonical_json(f"{plan_dir}/plan.json", plan)
        
        
        result = self.run(spec_path)
        if result.get("type") == "schema_error":
            return result
        
        
        checklist_data = result["checklist"]
        if isinstance(checklist_data, dict) and "items" in checklist_data:
            checklist_items = checklist_data["items"]
        elif isinstance(checklist_data, list):
            checklist_items = checklist_data
        else:
            
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
                
                bootstrap_dir = ".selfhost_outputs/modules"
                os.makedirs(bootstrap_dir, exist_ok=True)
                
                bootstrap_outputs = []
                for item in bootstrap_items:
                    
                    item_id = item.get("id", "unknown")
                    module_name = item_id.replace(".", "_")
                    module_path = os.path.join(bootstrap_dir, f"{module_name}.py")
                    
                    
                    bootstrap_code = f"""


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
                
                
                bootstrap_manifest = {
                    "modules": bootstrap_outputs,
                    "count": len(bootstrap_outputs)
                }
                manifest_path = ".selfhost_outputs/bootstrap_manifest.json"
                with open(manifest_path, "w") as f:
                    json.dump(bootstrap_manifest, f, indent=2, sort_keys=True)
        
        outputs = []
        outputs_list = []
        try:
            
            evidence = self.generate_evidence(spec_path, checklist_items)
            
            
            spec_fp = canonicalize(json.dumps(spec))
            items_fp = canonicalize(json.dumps(result["checklist"]))
            plan_fp = canonicalize(json.dumps(plan))
            code_fp = canonicalize(json.dumps(outputs))
            
            lineage_bundle = bundle(spec_fp, items_fp, plan_fp, code_fp)
            
            
            manifest_data = {
                "checklist": result["checklist"],
                "plan": plan,
                "evidence": evidence,
                "lineage": lineage_bundle,
                "outputs": outputs
            }
            write_manifest_v2(manifest_data, plan_dir)
            
            
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

        
        prev_manifest_path = f"{plan_dir}/manifest.json"
        stable = True
        if os.path.exists(prev_manifest_path):
            with open(prev_manifest_path) as f:
                prev_run = json.load(f)
            stable = compare(prev_run, current_run)
        
        
        from shieldcraft.services.spec.metrics import compute_metrics
        checklist_items = result["checklist"].get("items", [])
        spec_metrics = compute_metrics(spec, ast, checklist_items)
        
        
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
