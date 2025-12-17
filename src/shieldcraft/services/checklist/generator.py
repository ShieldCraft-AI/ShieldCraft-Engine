import hashlib
import logging
logger = logging.getLogger(__name__)
from .model import ChecklistModel
from .extractor import SpecExtractor
from .sections import SECTION_TITLES, ordered_sections


class ChecklistGenerator:
    def __init__(self):
        self.model = ChecklistModel()
        self.extractor = SpecExtractor()

    def generate(self, plan):
        checklist = []
        for idx, item in enumerate(plan, start=1):
            text = f"Implement {item['type']} from {item['ptr']}"
            checklist.append({
                # Use stable 8-char deterministic IDs for tasks
                "id": __import__('shieldcraft.services.checklist.idgen', fromlist=['stable_id']).stable_id(item['ptr'], text),
                "ptr": item['ptr'],
                "text": text,
                "hash": hashlib.sha256(text.encode()).hexdigest()
            })
        checklist = [self.model.normalize_item(i) for i in checklist]
        checklist = self.model.deterministic_sort(checklist)
        return checklist

    def extract_items(self, spec):
        raw_items = self.extractor.extract(spec)
        
        checklist = []
        for item in raw_items:
            ptr = item["ptr"]
            key = item["key"]
            text = self.render_task(item)
            checklist.append({
                "id": key,
                "ptr": ptr,
                "text": text
            })
        return checklist

    def normalize_item(self, item):
        return self.model.normalize_item(item)

    def build(self, spec, schema=None, ast=None, dry_run: bool = False, run_fuzz: bool = False, run_test_gate: bool = False, engine=None, interpreted_items=None):
        # Trace entry
        logger.debug("ChecklistGenerator.build: ENTRY")
        import json
        import os
        import hashlib
        import time
        from shieldcraft.services.preflight.preflight import run_preflight
        
        # Track timings for each pass
        timings = {}
        from shieldcraft.services.io.canonical_writer import write_canonical_json
        from shieldcraft.services.artifacts.lineage import build_lineage as build_artifact_lineage
        from shieldcraft.services.generator.invariants import check_invariants
        from shieldcraft.services.io.manifest_writer import write_manifest
        from shieldcraft.services.stability.stability import compute_run_signature, compare_to_previous
        from .plan import ExecutionPlan
        from .invariants import extract_invariants
        from .derived import infer_tasks
        from .constraints import propagate_constraints
        from .semantic import semantic_validations
        from .deps import extract_dependencies
        from .deps_tasks import dependency_tasks
        from .cross import cross_section_checks
        from .flow import compute_flow, flow_tasks
        from .order import ordering_constraints, assign_order_rank
        from .dedupe import dedupe_items
        from .collapse import collapse_items
        from .canonical import canonical_sort
        from .classify import classify_item
        from .severity import compute_severity
        from .idgen import synthesize_id
        from .meta import attach_metadata
        from .sanity import sanity_check
        from .validator import validate_cross_item_constraints
        from .grouping import group_items
        from .rollup import build_rollups
        from .evidence import build_evidence_bundle
        from .warnings import write_warnings
        from shieldcraft.services.diff.canonical_diff import diff
        from shieldcraft.services.diff.impact import impact_summary
        from shieldcraft.services.mapping.pointer_map import resolve
        from shieldcraft.services.rules.graph import build_graph, detect_cycles
        from shieldcraft.services.spec.dependency_contract import validate_dependencies
        from shieldcraft.services.plan.execution_plan import build_execution_plan
        from shieldcraft.services.ast.lineage import get_lineage_map

        # Build AST if not provided
        if not ast:
            try:
                logger.debug("ChecklistGenerator.build: building AST")
            except Exception:
                pass
            from shieldcraft.services.ast.builder import ASTBuilder
            ast_builder = ASTBuilder()
            ast = ast_builder.build(spec)
            try:
                logger.debug("ChecklistGenerator.build: AST built")
            except Exception:
                pass

        # Make checklist context available to generator via engine (plumbing only)
        context = None
        if engine is not None:
            context = getattr(engine, 'checklist_context', None)

        # Phase 11A: Synthesize missing known defaults and enforce tiers
        from shieldcraft.services.spec.defaults import synthesize_missing_spec_fields
        from shieldcraft.services.checklist.tier_enforcement import enforce_tiers

        # Capture missing sections (and record BLOCKERs/DIAGNOSTICs) before synthesis
        missing_items = enforce_tiers(spec, context)

        # Synthesize defaults deterministically
        try:
            logger.debug("ChecklistGenerator.build: synthesizing defaults")
        except Exception:
            pass
        spec, synthesized_keys = synthesize_missing_spec_fields(spec)
        try:
            logger.debug(f"ChecklistGenerator.build: synthesized keys={synthesized_keys}")
        except Exception:
            pass

        # For any synthesized Tier A/B keys, record a DIAGNOSTIC checklist item and create explainability metadata
        synthesized_items = []
        for key in synthesized_keys:
            # Emit events for synthesized defaults: Tier A -> BLOCKER + DIAGNOSTIC, Tier B -> DIAGNOSTIC
            try:
                if context:
                    try:
                        tier = "A" if key in ("metadata", "agents", "evidence_bundle") else ("B" if key in ("determinism", "artifact_contract", "generation_mappings", "security") else "C")
                        ev_name = f"G_SYNTHESIZED_DEFAULT_{key.upper()}"
                        if tier == "A":
                            try:
                                context.record_event(ev_name, "compilation", "BLOCKER", message=f"Synthesized Tier A default for missing section: {key}", evidence={"section": key})
                            except Exception:
                                pass
                            try:
                                context.record_event(ev_name, "compilation", "DIAGNOSTIC", message=f"Synthesized default for missing section: {key}", evidence={"section": key})
                            except Exception:
                                pass
                        elif tier == "B":
                            try:
                                context.record_event(ev_name, "compilation", "DIAGNOSTIC", message=f"Synthesized Tier B default for missing section: {key}", evidence={"section": key})
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass

            # Determine tier for the synthesized key (ensure tier is set for later use)
            tier = "A" if key in ("metadata", "agents", "evidence_bundle") else ("B" if key in ("determinism", "artifact_contract", "generation_mappings", "security") else "C")

            # Build a deterministic checklist diagnostic for the synthesized default (include provenance metadata)
            synth_item = {
                "ptr": f"/{key}",
                "text": f"SYNTHESIZED DEFAULT: injected default for missing section {key}",
                "meta": {
                    "section": key,
                    "tier": tier,
                    "synthesized_default": True,
                    "source": "default",
                    "justification": f"safe_default_{key}",
                    "justification_ptr": f"/{key}",
                    "inference_type": "safe_default",
                },
                "severity": "high" if tier == "A" else "medium",
                "classification": "compiler",
            }
            synthesized_items.append(synth_item)

        # We'll append both tier-enforcement missing items and synthesized items to raw_items after extraction so they flow through the pipeline
        _pre_extraction_missing_items = missing_items + synthesized_items

        # Inference ceiling enforcement: ensure Tier A syntheses have an accompanying explicit missing-item
        try:
            from shieldcraft.services.checklist.tier_enforcement import TIER_A
            synthesized_set = set(synthesized_keys or [])
            for k in synthesized_set:
                if k in TIER_A:
                    # There must be a pre-extraction missing item for this section
                    if not any(((it.get('meta') or {}).get('section') == k) for it in _pre_extraction_missing_items):
                        raise AssertionError(f"Compiler invariant violated: Tier A synthesized key {k} without explicit missing-item explainability")
                # Attach provenance of the synthesized defaults into spec-level metadata so finalizer can expose it
                if hasattr(spec, 'setdefault'):
                    if '_synthesized_metadata' in spec:
                        # already attached in defaults; nothing to do
                        pass
                    else:
                        spec.setdefault('_synthesized_metadata', {})
                        for k2 in synthesized_keys:
                            spec['_synthesized_metadata'][k2] = {'source': 'default', 'justification': f'safe_default_{k2}', 'inference_type': 'safe_default'}
        except Exception:
            # Failures here must be visible during testing; do not silently continue in production
            raise

        # Run speculative spec fuzzing gate to detect ambiguity/contradiction
        if run_fuzz:
            try:
                from shieldcraft.services.validator.spec_gate import enforce_spec_fuzz_stability
                enforce_spec_fuzz_stability(spec, self)
            except RuntimeError as e:
                # Do not raise: record event and return a partial invalid result so engine can finalize
                try:
                    if context:
                        try:
                            context.record_event("G9_GENERATOR_RUN_FUZZ_GATE", "generation", "BLOCKER", message="spec fuzz stability failed", evidence={"error": str(e)})
                        except Exception:
                            pass
                except Exception:
                    pass
                # Return a partial result indicating invalid generation
                return {
                    "valid": False,
                    "reason": "spec_fuzz_stability_failed",
                    "items": [],
                    "preflight": {},
                }
            except Exception:
                # Non-fatal: if fuzzing/gate unavailable, continue
                pass
        
        # Build lineage map from AST
        lineage_map = get_lineage_map(ast)
        
        # Extract items using AST traversal
        raw_items = self._extract_from_ast(ast)
        try:
            logger.debug(f"ChecklistGenerator.build: raw_items extracted count={len(raw_items)}")
        except Exception:
            pass

        # Append any pre-extraction missing items produced by tier enforcement
        try:
            raw_items.extend(_pre_extraction_missing_items)
        except Exception:
            pass

        # Spec sufficiency diagnostics: emit DIAGNOSTIC items explaining insufficiency
        try:
            logger.debug("ChecklistGenerator.build: running spec sufficiency checks")
        except Exception:
            pass
        try:
            from shieldcraft.services.spec.analysis import check_spec_sufficiency
            findings = check_spec_sufficiency(spec)
            for f in findings:
                # record diagnostic event
                try:
                    if context:
                        try:
                            context.record_event(f"G_SPEC_INSUFFICIENCY_{f['code']}", "compilation", "DIAGNOSTIC", message=f['message'], evidence={"pointer": f.get('pointer')})
                        except Exception:
                            pass
                except Exception:
                    pass
                # Append as a checklist diagnostic item
                raw_items.append({
                    "ptr": f.get("pointer") or "/",
                    "text": f"SPEC INSUFFICIENT: {f.get('message')}",
                    "meta": {"insufficiency": f.get('code')},
                    "severity": "medium" if f.get('severity') == 'medium' else 'low',
                    "classification": "compiler",
                    "synthesized_default": False,
                })
        except Exception:
            pass
        
        # Attach lineage_id to each item
        try:
            logger.debug("ChecklistGenerator.build: attaching lineage and extracting items")
        except Exception:
            pass
        for item in raw_items:
            ptr = item.get("ptr", "/")
            try:
                logger.debug(f"ChecklistGenerator.build: processing raw item ptr={ptr}")
            except Exception:
                pass
            if ptr in lineage_map:
                item["lineage_id"] = lineage_map[ptr]
                # Find node to get type
                try:
                    node = ast.find(ptr)
                    if node:
                        item["source_node_type"] = node.type
                except Exception:
                    item["source_node_type"] = None
            else:
                # For interpreted items, we may set ptr to '/' to avoid missing lineage
                if item.get("origin") == "interpreted":
                    item["ptr"] = item.get("ptr", "/") or "/"
                    if item["ptr"] in lineage_map:
                        item["lineage_id"] = lineage_map[item["ptr"]]
                        item["source_node_type"] = "interpreted"
                    else:
                        # As a last resort attach a synthetic lineage id
                        item["lineage_id"] = f"interpreted:{item.get('id')}"
                        item["source_node_type"] = "interpreted"
                else:
                    # Missing lineage id: record a diagnostic event and attach synthetic lineage id (do not raise)
                    try:
                        if context:
                            try:
                                context.record_event("G10_GENERATOR_PREP_MISSING", "generation", "DIAGNOSTIC", message=f"Missing lineage_id for item at pointer: {ptr}")
                            except Exception:
                                pass
                    except Exception:
                        pass
                    # Attach a synthetic lineage id to allow generation to continue
                    item["lineage_id"] = f"missing_lineage:{ptr}"
                    item["source_node_type"] = item.get("source_node_type") or "unknown"
        
        # Add constraint tasks
        constraint_items = propagate_constraints(spec)
        raw_items.extend(constraint_items)

        # Merge interpreted items (if any) into raw_items early in the pipeline
        if interpreted_items:
            for it in interpreted_items:
                # Map interpreted ChecklistItem v1 to internal raw item shape
                ri = {
                    "ptr": it.get("evidence_ref", {}).get("ptr") or "/",
                    "id": str(it.get("id") or _det_hash(it.get("claim", "")[:24])),
                    "text": it.get("claim") or it.get("obligation"),
                    "origin": {"source": "interpreted"},
                    "obligation": it.get("obligation"),
                    "claim": it.get("claim"),
                    "risk_if_false": it.get("risk_if_false"),
                    "confidence": it.get("confidence"),
                    "evidence_ref": it.get("evidence_ref"),
                    "meta": {},
                }
                raw_items.append(ri)
        
        # Add semantic validation tasks
        semantic_items = semantic_validations(spec)
        raw_items.extend(semantic_items)
        
        # Add dependency tasks
        dep_edges = extract_dependencies(spec)
        dep_items = dependency_tasks(dep_edges)
        raw_items.extend(dep_items)
        
        # Add cross-section checks
        cross_items = cross_section_checks(spec)
        raw_items.extend(cross_items)
        
        # Add flow tasks
        flows = compute_flow(spec)
        flow_items = flow_tasks(flows)
        raw_items.extend(flow_items)
        
        # Add ordering constraints
        order_items = ordering_constraints(raw_items)
        raw_items.extend(order_items)
        
        # Enrich with classification and severity
        enriched = []
        for it in raw_items:
            # Skip non-dict items (constraints)
            if not isinstance(it, dict):
                continue
            it["classification"] = classify_item(it)
            it["severity"] = compute_severity(it)
            enriched.append(it)
        try:
            logger.debug(f"ChecklistGenerator.build: enriched count={len(enriched)}")
        except Exception:
            pass
        
        # Dedupe, collapse, and canonically sort
        merged = enriched
        merged = dedupe_items(merged)
        try:
            logger.debug(f"ChecklistGenerator.build: after dedupe count={len(merged)}")
        except Exception:
            pass
        merged = collapse_items(merged)
        try:
            logger.debug(f"ChecklistGenerator.build: after collapse count={len(merged)}")
        except Exception:
            pass
        final_items = canonical_sort(merged)
        try:
            logger.debug(f"ChecklistGenerator.build: after canonical_sort final_items count={len(final_items)}")
        except Exception:
            pass
        
        # Assign order rank
        for it in final_items:
            it["order_rank"] = assign_order_rank(it)
        
        # Annotate items with guidance before synthesizing a final stable id
        try:
            from shieldcraft.services.guidance.checklist import annotate_items, enrich_with_confidence_and_evidence
            try:
                logger.debug("ChecklistGenerator.build: annotating items")
            except Exception:
                pass
            annotate_items(final_items)
            try:
                logger.debug("ChecklistGenerator.build: enriching items with confidence and evidence")
            except Exception:
                pass
            try:
                final_items = enrich_with_confidence_and_evidence(final_items, spec)
                try:
                    logger.debug(f"ChecklistGenerator.build: after enrich, items count={len(final_items)}")
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

        # Synthesize IDs with namespace using enriched intent/evidence so ids remain stable
        namespace = spec.get("metadata", {}).get("id_namespace", "default")
        for it in final_items:
            it["id"] = synthesize_id(it, namespace)
        
        # Invariant validation pass
        # Extract invariants from AST if available, otherwise from spec
        spec_invariants = extract_invariants(ast if ast else spec)
        
        # Also extract spec-level invariants
        from shieldcraft.services.spec.invariants import extract_spec_invariants
        spec_level_invariants = extract_spec_invariants(spec)
        
        # Merge AST and spec invariants
        all_invariants = spec_invariants + spec_level_invariants
        
        # Attach spec invariants to items
        for item in final_items:
            item["invariants_from_spec"] = []
            for inv in spec_level_invariants:
                # Check if item relates to this invariant (same pointer prefix)
                item_ptr = item.get("ptr", "")
                inv_ptr = inv.get("spec_ptr", "")
                if item_ptr.startswith(inv_ptr) or inv_ptr.startswith(item_ptr):
                    item["invariants_from_spec"].append(inv)
        
        # Evaluate invariants using evaluate_invariant
        from .invariants import evaluate_invariant
        
        invariant_violations = []
        for invariant in all_invariants:
            # Normalize invariant fields (support mixed shapes from different extractors)
            inv_ptr = invariant.get("spec_ptr") or invariant.get("pointer") or ""
            expr = invariant.get("expr") or invariant.get("constraint") or ""

            # Build evaluation context
            eval_context = {
                "items": final_items,
                "spec": spec
            }

            # Evaluate invariant expression (if any)
            result = True
            if expr:
                result = evaluate_invariant(expr, eval_context)
            else:
                # No expression: treat as unknown/malformed invariant -> safe default
                # Record explainability in eval_context so callers can attach metadata
                try:
                    if isinstance(eval_context, dict):
                        ctxmap = eval_context.setdefault('_invariant_eval_explain', {})
                        ctxmap[expr] = {'source': 'default_true', 'justification': 'unknown_expr_safe_default'}
                except Exception:
                    pass

            # Prepare a single diagnostic (if needed) per invariant; don't mutate final_items while iterating
            pending_diag = None
            explainability = None
            if not (expr.startswith("exists(") or expr.startswith("count(") or expr.startswith("unique(")):
                explainability = {"source": "default_true", "justification": "unknown_expr_safe_default", "inference_type": "safe_default"}
                pending_diag = {
                    "ptr": inv_ptr or "/",
                    "text": f"INVARIANT_SAFE_DEFAULT: {expr}",
                    "meta": {"invariant_expr": expr, "explainability": explainability, "inference_type": "safe_default"},
                    "severity": "medium",
                    "classification": "compiler",
                }

            # Attach result to items that match this invariant
            for item in list(final_items):
                item_ptr = item.get("ptr", "")
                if inv_ptr and (item_ptr.startswith(inv_ptr) or inv_ptr.startswith(item_ptr)):
                    if "meta" not in item:
                        item["meta"] = {}
                    if "invariant_results" not in item["meta"]:
                        item["meta"]["invariant_results"] = []
                    # Always attach explainability metadata for invariants (evaluated or defaulted)
                    inv_record = {"invariant_id": invariant.get("id"), "result": result}
                    if explainability:
                        inv_record["explainability"] = explainability
                    else:
                        inv_record["explainability"] = {"source": "evaluated_expr", "justification": "expr_evaluated", "inference_type": "structural"}
                    item["meta"]["invariant_results"].append(inv_record)

            # If we prepared a diagnostic, append it once and record an event
            if pending_diag is not None:
                try:
                    pending_diag["id"] = synthesize_id(pending_diag, namespace)
                except Exception:
                    pending_diag["id"] = f"diag::{hash(str(pending_diag))&0xffff:04x}"
                # Ensure diagnostic pointer is unique so it survives cross-item validation
                try:
                    pending_diag["ptr"] = f"/_diagnostics/invariant/{pending_diag['id']}"
                except Exception:
                    pending_diag["ptr"] = f"/_diagnostics/invariant/unknown"
                final_items.append(pending_diag)
                try:
                    logger.debug(f"ChecklistGenerator.build: appended invariant diag item id={pending_diag.get('id')} expr={expr}")
                except Exception:
                    pass
                try:
                    if context and getattr(context, 'record_event', None):
                        try:
                            context.record_event(f"G_INVARIANT_SAFE_DEFAULT", "compilation", "DIAGNOSTIC", message=f"Invariant defaulted: {expr}", evidence={"pointer": inv_ptr})
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    logger.debug(f"ChecklistGenerator.build: recorded G_INVARIANT_SAFE_DEFAULT for expr={expr}")
                except Exception:
                    pass

            # Record violations
            if not result:
                invariant_violations.append({
                    "invariant_id": invariant.get("id"),
                    "spec_ptr": inv_ptr,
                    "expr": expr,
                    "severity": invariant.get("severity", "medium")
                })
        
        # Legacy violation checking for backward compatibility
        for invariant in all_invariants:
            # Check each invariant against checklist items
            for item in final_items:
                # Verify constraints
                if invariant["type"] == "must":
                    # Must constraint: item must satisfy condition
                    if not self._check_invariant_satisfied(item, invariant):
                        invariant_violations.append({
                            "item_id": item.get("id", "unknown"),
                            "invariant_pointer": invariant["pointer"],
                            "invariant_type": invariant["type"],
                            "constraint": invariant["constraint"]
                        })
                elif invariant["type"] == "forbid":
                    # Forbid constraint: item must not match condition
                    if self._check_invariant_forbidden(item, invariant):
                        invariant_violations.append({
                            "item_id": item.get("id", "unknown"),
                            "invariant_pointer": invariant["pointer"],
                            "invariant_type": invariant["type"],
                            "constraint": invariant["constraint"]
                        })
        
        # Cycle detection pass - before derived tasks
        from .graph import build_graph, get_cycle_members
        graph_result = build_graph(final_items)
        cycles = graph_result["cycles"]
        cycle_members = get_cycle_members(cycles)
        
        # Mark items involved in cycles
        for item in final_items:
            item_id = item.get("id")
            if item_id in cycle_members:
                if "meta" not in item:
                    item["meta"] = {}
                item["meta"]["cycle"] = True
        
        # Derived tasks pass - after invariants and cycles
        all_derived = []
        for item in final_items:
            derived_tasks = infer_tasks(item)
            for derived in derived_tasks:
                # Ensure derived task has stable ID
                if "id" not in derived:
                    derived["id"] = synthesize_id(derived, namespace)
                # Ensure derived task has order_rank
                if "order_rank" not in derived:
                    derived["order_rank"] = assign_order_rank(derived)
                all_derived.append(derived)
        
        # Create resolve-cycle tasks if cycles detected
        if cycles:
            for cycle in cycles:
                # Create one resolve-cycle task per cycle
                cycle_task = {
                    "id": f"resolve-cycle-{hash(tuple(sorted(cycle))) % 10000:04d}",
                    "type": "resolve-cycle",
                    "description": f"Resolve circular dependency: {' -> '.join(cycle)}",
                    "cycle_items": cycle,
                    "meta": {
                        "cycle": True,
                        "cycle_length": len(cycle)
                    }
                }
                all_derived.append(cycle_task)
        
        # Add derived tasks to main list
        try:
            logger.debug(f"ChecklistGenerator.build: derived tasks count={len(all_derived)}")
        except Exception:
            pass
        final_items.extend(all_derived)
        
        # Ensure interpreted items persist: append any interpreted_items not present
        try:
            if interpreted_items:
                existing_ids = {it.get("id") for it in final_items if it.get("id")}
                for uit in interpreted_items:
                    uid = str(uit.get("id"))
                    if uid in existing_ids:
                        continue
                    # Create an item from interpreted ChecklistItem v1
                    conf = (uit.get("confidence") or "low").lower()
                    sev = "low" if conf == "low" else ("high" if conf == "high" else "medium")
                    new_it = {
                        "id": uid,
                        "ptr": uit.get("evidence_ref", {}).get("ptr") or "/",
                        "text": uit.get("claim") or uit.get("obligation"),
                        "origin": {"source": "interpreted"},
                        "claim": uit.get("claim"),
                        "obligation": uit.get("obligation"),
                        "risk_if_false": uit.get("risk_if_false"),
                        "confidence": conf,
                        "severity": sev,
                        "meta": {},
                        "category": "misc",
                        "classification": "core",
                    }
                    final_items.append(new_it)
        except Exception:
            pass

        # Attach metadata
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        decorated = []
        for it in final_items:
            decorated.append(attach_metadata(it, product_id))
        
        # Sanity check
        decorated = sanity_check(decorated)
        
        # Cross-item validation
        decorated, validation_warnings = validate_cross_item_constraints(decorated)

        # Annotate checklist items deterministically (no change to order)
        try:
            from shieldcraft.services.guidance.checklist import annotate_items, enrich_with_confidence_and_evidence
            annotate_items(decorated)
            # Add confidence & evidence metadata to items (enriches provenance without changing behavior)
            try:
                decorated = enrich_with_confidence_and_evidence(decorated, spec)
            except Exception:
                pass
        except Exception:
            pass
        
        # Group items
        grouped = group_items(decorated)
        
        # Build rollups
        try:
            logger.debug("ChecklistGenerator.build: building rollups")
        except Exception:
            pass
        rollups = build_rollups(grouped)
        try:
            logger.debug(f"ChecklistGenerator.build: rollups built")
        except Exception:
            pass
        
        # Write warnings
        write_warnings(product_id, validation_warnings)
        
        # Run preflight checks
        try:
            logger.debug("ChecklistGenerator.build: running preflight")
        except Exception:
            pass
        if schema is None:
            schema = {"type": "object"}  # default minimal schema
        preflight = run_preflight(spec, schema, decorated)
        try:
            logger.debug(f"ChecklistGenerator.build: preflight result={preflight}")
        except Exception:
            pass
        # Enforce that checklist items have attached, valid tests (halt if not)
        if run_test_gate:
            try:
                from shieldcraft.services.validator.test_gate import enforce_tests_attached
                enforce_tests_attached(decorated)
            except RuntimeError as e:
                # Do not raise: record event and return a partial invalid result so engine can finalize
                try:
                    if context:
                        try:
                            context.record_event("G11_RUN_TEST_GATE", "generation", "BLOCKER", message="tests missing or invalid", evidence={"error": str(e)})
                        except Exception:
                            pass
                except Exception:
                    pass
                return {
                    "valid": False,
                    "reason": "tests_missing_or_invalid",
                    "items": decorated,
                    "preflight": preflight,
                }
            except Exception:
                # Non-fatal: if test gate unavailable, continue
                pass

        # Optionally attach candidate test refs for items (non-authoritative)
        # Before expanding tests, allow personas to evaluate and constrain/veto items
        try:
            if engine is not None and getattr(engine, "persona_enabled", False):
                from shieldcraft.persona.persona_registry import find_personas_for_phase
                from shieldcraft.persona.persona_evaluator import evaluate_personas
                from shieldcraft.services.validator.persona_gate import enforce_persona_veto

                personas = find_personas_for_phase("checklist")
                persona_res = evaluate_personas(engine, personas, decorated, phase="checklist")
                # Apply persona constraints in the engine-controlled scope deterministically
                for c in persona_res.get("constraints", []):
                    iid = c.get("item_id")
                    iptr = c.get("item_ptr")
                    setter = c.get("set", {})
                    # Find matching item and apply permitted setters
                    # Try to match by id or ptr first; otherwise fall back to matching by the original rule match
                    matched = False
                    for item in decorated:
                        if (iid is not None and item.get("id") == iid) or (iptr is not None and item.get("ptr") == iptr):
                            matched = True
                            # If persona evaluator flagged this constraint as disallowed, surface it
                            if c.get("disallowed"):
                                item.setdefault("meta", {}).setdefault("persona_constraints_disallowed", []).append({"persona": c.get("persona"), "attempt": setter})
                                try:
                                    if context:
                                        try:
                                            from shieldcraft.util.json_canonicalizer import canonicalize
                                            context.record_event("G15_PERSONA_CONSTRAINT_DISALLOWED", "generation", "DIAGNOSTIC", message=f"persona attempted disallowed mutation", evidence={"persona": c.get("persona"), "attempt": canonicalize(setter)})
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                break
                    # If not matched by id/ptr, fall back to re-matching using the original match rule if present
                    if not matched and c.get("match"):
                        for item in decorated:
                            if all(item.get(k) == v for k, v in c.get("match", {}).items()):
                                if c.get("disallowed"):
                                    item.setdefault("meta", {}).setdefault("persona_constraints_disallowed", []).append({"persona": c.get("persona"), "attempt": setter})
                                    try:
                                        if context:
                                            try:
                                                from shieldcraft.util.json_canonicalizer import canonicalize
                                                context.record_event("G15_PERSONA_CONSTRAINT_DISALLOWED", "generation", "DIAGNOSTIC", message=f"persona attempted disallowed mutation", evidence={"persona": c.get("persona"), "attempt": canonicalize(setter)})
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass
                                continue
                    # If matched above we already processed; otherwise apply permitted setters normally
                    for item in decorated:
                        if (iid is not None and item.get("id") == iid) or (iptr is not None and item.get("ptr") == iptr) or (c.get("match") and all(item.get(k) == v for k, v in c.get("match", {}).items())):
                            if c.get("disallowed"):
                                # already handled
                                continue
                            for sk, sv in setter.items():
                                # Forbid mutating identifiers and semantic fields that affect checklist outcomes
                                forbidden = set(["id", "ptr", "generated", "artifact", "severity", "refusal", "outcome"])
                                if sk in forbidden:
                                    item.setdefault("meta", {}).setdefault("persona_constraints_disallowed", []).append({"persona": c.get("persona"), "attempt": {sk: sv}})
                                    # Record a DIAGNOSTIC to make the disallowed attempt visible
                                    try:
                                        from shieldcraft.util.json_canonicalizer import canonicalize
                                        if context:
                                            try:
                                                context.record_event("G15_PERSONA_CONSTRAINT_DISALLOWED", "generation", "DIAGNOSTIC", message=f"persona attempted disallowed mutation: {sk}", evidence={"persona": c.get("persona"), "attempt": canonicalize({sk: sv})})
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass
                                elif sk == "meta":
                                    item.setdefault("meta", {}).setdefault("persona_constraints_applied", []).append({"persona": c.get("persona"), "set": sv})
                                else:
                                    item[sk] = sv
                            for sk, sv in setter.items():
                                # Forbid mutating identifiers and semantic fields that affect checklist outcomes
                                forbidden = set(["id", "ptr", "generated", "artifact", "severity", "refusal", "outcome"])
                                if sk in forbidden:
                                    item.setdefault("meta", {}).setdefault("persona_constraints_disallowed", []).append({"persona": c.get("persona"), "attempt": {sk: sv}})
                                    # Record a DIAGNOSTIC to make the disallowed attempt visible
                                    try:
                                        from shieldcraft.util.json_canonicalizer import canonicalize
                                        if context:
                                            try:
                                                context.record_event("G15_PERSONA_CONSTRAINT_DISALLOWED", "generation", "DIAGNOSTIC", message=f"persona attempted disallowed mutation: {sk}", evidence={"persona": c.get("persona"), "attempt": canonicalize({sk: sv})})
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass
                                elif sk == "meta":
                                    item.setdefault("meta", {}).setdefault("persona_constraints_applied", []).append({"persona": c.get("persona"), "set": sv})
                                else:
                                    item[sk] = sv
                # Enforce vetoes if any persona emitted a veto (advisory-only under Phase 15)
                sel = enforce_persona_veto(engine)
                # If a veto was present, record advisory event in generation phase for visibility
                if sel is not None:
                    try:
                        if context:
                            try:
                                context.record_event("G7_PERSONA_VETO", "generation", "DIAGNOSTIC", message="persona veto advisory (non-authoritative)", evidence={"persona_id": sel.get('persona_id'), "code": sel.get('code')})
                            except Exception:
                                pass
                    except Exception:
                        pass
        except RuntimeError as e:
            try:
                if context:
                    try:
                        context.record_event("G12_PERSONA_VETO_ENFORCEMENT", "generation", "REFUSAL", message="persona veto at generator", evidence={"error": str(e)})
                    except Exception:
                        pass
            except Exception:
                pass
            raise
        except Exception:
            # Do not let persona evaluation failures break checklist generation
            pass

        try:
            try:
                logger.debug("ChecklistGenerator.build: about to discover_tests")
            except Exception:
                pass
            from shieldcraft.verification.test_expander import expand_tests_for_item
            from shieldcraft.verification.test_registry import discover_tests
            test_map = discover_tests()
            try:
                logger.debug("ChecklistGenerator.build: discover_tests returned")
            except Exception:
                pass
            for it in decorated:
                try:
                    exp = expand_tests_for_item(it, test_map)
                    if exp.get("candidates"):
                        it.setdefault("meta", {})["candidate_tests"] = exp.get("candidates")
                except Exception:
                    pass
        except Exception:
            pass
        # Determinism marker: if a run seed exists, attach a small per-item marker
        try:
            from shieldcraft.verification.seed_manager import get_seed
            if engine is not None:
                run_seed = get_seed(engine, "run")
                if run_seed:
                    for it in decorated:
                        sm = __import__("hashlib").sha256((run_seed + ":" + it.get("id", "")).encode("utf-8")).hexdigest()[:8]
                        it.setdefault("meta", {})["determinism_marker"] = sm
        except Exception:
            pass

        plan = ExecutionPlan(decorated)
        plan.stage_pass1(decorated)
        try:
            logger.debug(f"ChecklistGenerator.build: staged pass1 count={len(plan.pass1)}")
        except Exception:
            pass

        # pass 2: invariants
        inv_items = extract_invariants(spec)
        plan.stage_pass2(inv_items)

        # pass 3: derived
        d_items = []
        for it in decorated:
            d_items.extend(infer_tasks(it))
        plan.stage_pass3(d_items)

        # normalize + classify + id assign
        normalized = [self.normalize_item(i) for i in plan.merged()]

        # group + sort (existing logic)
        groups = {}
        for item in normalized:
            c = item["category"]
            groups.setdefault(c, []).append(item)

        for c in groups:
            groups[c] = sorted(groups[c], key=lambda x: x["id"])

        ordered = []
        for c in ordered_sections(groups.keys()):
            ordered.append((c, groups[c]))

        plan.stage_pass4([i for _, g in ordered for i in g])

        # Compute lineage (artifact lineage, not AST lineage)
        items_hash = hashlib.sha256(json.dumps(decorated, sort_keys=True).encode("utf-8")).hexdigest()
        spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode("utf-8")).hexdigest()
        lineage = build_artifact_lineage(product_id, spec_hash, items_hash)
        
        # Build evidence
        evidence = build_evidence_bundle(product_id, decorated, rollups)
        # Ensure every item has confidence, evidence, inferred flags and intent category
        try:
            from shieldcraft.services.guidance.checklist import ensure_item_fields
            decorated = ensure_item_fields(decorated)
        except Exception:
            pass
        
        # Check invariants
        inv_ok, inv_violations = check_invariants({
            "items": decorated,
            "rollups": rollups,
            "evidence": evidence,
            "lineage": lineage
        })
        
        # Compute diff report
        diff_report = diff([], decorated)
        
        # Compute impact score
        diff_score = impact_summary(diff_report)
        
        # Attach target paths to diff elements
        for group in ["added","removed","changed"]:
            for elem in diff_report[group]:
                elem["target_path"] = resolve(elem["ptr"], product_id)
        
        # Build rule graph
        rc = spec.get("rules_contract", {})
        rules = rc.get("rules", []) if rc else []
        rule_graph = build_graph(rules)
        cycles = detect_cycles(rule_graph)
        
        # Validate dependencies
        dep_ok, dep_viol = validate_dependencies(spec)
        
        # Build execution plan
        exec_plan = build_execution_plan(spec)
        
        # Compute resolution chains for derived tasks
        from .resolution_chain import build_chain
        resolution_chains = build_chain(decorated)
        
        # Build task ancestry
        from .ancestry import build_ancestry
        ancestry = build_ancestry(decorated)
        
        # Attach ancestry to items metadata
        for item in decorated:
            item_id = item.get("id")
            if item_id in ancestry:
                if "meta" not in item:
                    item["meta"] = {}
                item["meta"]["ancestry"] = ancestry[item_id]
        
        # Register all IDs in global registry
        from .id_registry import create_registry
        id_registry = create_registry(decorated)
        
        # Extract implicit dependencies
        from .implicit_deps import extract_implicit_deps
        implicit_deps = extract_implicit_deps(spec)

        # Check contract enforcement
        if not preflight["contract_ok"]:
            # still return artifacts but mark them as invalid
            result = {
                "valid": False,
                "reason": "generation_contract_failed",
                "preflight": preflight,
                "items": decorated,
                "invariants_ok": inv_ok,
                "invariant_violations": inv_violations,
                "diff": diff_report,
                "diff_score": diff_score,
                "rule_graph": rule_graph,
                "rule_graph_cycles": cycles,
                "dependency_ok": dep_ok,
                "dependency_violations": dep_viol,
                "execution_plan": exec_plan
            }
            try:
                if engine is not None:
                    from shieldcraft.verification.seed_manager import snapshot
                    try:
                        from shieldcraft.services.governance.determinism import DeterminismEngine
                        de = DeterminismEngine()
                        ast_summary = []
                        try:
                            ast_summary = sorted([n.ptr for n in ast.walk()])
                        except Exception:
                            ast_summary = []
                        ast_fp = de.hash(de.canonicalize(ast_summary))
                        result["_determinism"] = {"seeds": snapshot(engine), "spec": spec, "ast_summary": ast_fp, "checklist": result}
                    except Exception:
                        result["_determinism"] = {"seeds": snapshot(engine), "spec": spec, "ast_summary": None, "checklist": result}
            except Exception:
                pass
            try:
                if engine is not None and getattr(engine, 'checklist_context', None):
                    try:
                        engine.checklist_context.record_event("G13_GENERATION_CONTRACT_FAILED", "generation", "BLOCKER", message="generation contract failed")
                    except Exception:
                        pass
            except Exception:
                pass
            return result

        result = {
            "valid": True,
            "items": decorated,
            "grouped": grouped,
            "rollups": rollups,
            "evidence": evidence,
            "preflight": preflight,
            "lineage": lineage,
            "invariants_ok": inv_ok,
            "invariant_violations": inv_violations,
            "diff": diff_report,
            "diff_score": diff_score,
            "rule_graph": rule_graph,
            "rule_graph_cycles": cycles,
            "dependency_ok": dep_ok,
            "dependency_violations": dep_viol,
            "execution_plan": exec_plan
        }
        
        # Write manifest
        if not dry_run:
            write_manifest(product_id, result)
        
        # Compute stability
        signature = compute_run_signature(result)
        result["stable"] = compare_to_previous(product_id, signature)
        # Attach determinism snapshot if engine provided
        try:
            if engine is not None:
                from shieldcraft.verification.seed_manager import snapshot
                try:
                    # Avoid storing non-serializable AST objects; record a lightweight AST summary hash instead
                    from shieldcraft.services.governance.determinism import DeterminismEngine
                    de = DeterminismEngine()
                    ast_summary = []
                    try:
                        ast_summary = sorted([n.ptr for n in ast.walk()])
                    except Exception:
                        ast_summary = []
                    ast_fp = de.hash(de.canonicalize(ast_summary))
                    result["_determinism"] = {"seeds": snapshot(engine), "spec": spec, "ast_summary": ast_fp, "checklist": result}
                except Exception:
                    pass
        except Exception:
            pass
        
        return result

    def _validate_invariant(self, item, expression):
        """
        Invariant validation - intentionally permissive.
        
        INTENTIONAL: Always returns True (no violation).
        Real invariant parsing and evaluation would require:
        1. Expression parser (e.g., "sections[*].tasks > 0")
        2. Safe evaluation engine
        3. Item context binding
        
        Current behavior: All invariants pass validation.
        """
        return True

    def compile(self, spec):
        grouped = self.build(spec)
        return self.render_markdown(grouped)

    def render_markdown(self, grouped):
        from .writer import ChecklistWriter
        w = ChecklistWriter()
        return w.render(grouped)

    def render_task(self, item):
        ptr = item["ptr"]
        v = item["value"]

        # Structural categories
        if isinstance(v, dict):
            return f"Implement object at {ptr}"
        if isinstance(v, list):
            return f"Implement list at {ptr}"

        # Scalars — detect type
        if isinstance(v, bool):
            return f"Implement boolean at {ptr}: {v}"
        return f"Implement value at {ptr}"
    
    def _check_invariant_satisfied(self, item, invariant):
        """Check if item satisfies a 'must' invariant."""
        constraint = invariant["constraint"]
        # Simple string matching for now
        if isinstance(constraint, str):
            # Check if constraint appears in item text or ptr
            item_text = item.get("text", "")
            item_ptr = item.get("ptr", "")
            return constraint.lower() in item_text.lower() or constraint.lower() in item_ptr.lower()
        return True
    
    def _check_invariant_forbidden(self, item, invariant):
        """Check if item violates a 'forbid' invariant."""
        constraint = invariant["constraint"]
        # Simple string matching for now
        if isinstance(constraint, str):
            # Check if forbidden pattern appears in item
            item_text = item.get("text", "")
            item_ptr = item.get("ptr", "")
            return constraint.lower() in item_text.lower() or constraint.lower() in item_ptr.lower()
        return False

        return f"Implement scalar at {ptr}"
    
    def _extract_from_ast(self, ast):
        """Extract checklist items using AST traversal."""
        items = []
        
        # Walk all nodes in AST
        for node in ast.walk():
            if node.type == "dict_entry":
                # Extract the value regardless of type (object, list, scalar)
                value_obj = node.value.get("value")
                item = {
                    "ptr": node.ptr,
                    "key": node.value.get("key", ""),
                    "value": value_obj,
                }
                # Use the generator's render_task to produce deterministic text
                item["text"] = self.render_task(item)
                items.append(item)
        
        return items
