import hashlib
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

    def build(self, spec, schema=None, ast=None):
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
            from shieldcraft.services.ast.builder import ASTBuilder
            ast_builder = ASTBuilder()
            ast = ast_builder.build(spec)
        
        # Build lineage map from AST
        lineage_map = get_lineage_map(ast)
        
        # Extract items using AST traversal
        raw_items = self._extract_from_ast(ast)
        
        # Attach lineage_id to each item
        for item in raw_items:
            ptr = item.get("ptr", "/")
            if ptr in lineage_map:
                item["lineage_id"] = lineage_map[ptr]
                # Find node to get type
                node = ast.find(ptr)
                if node:
                    item["source_node_type"] = node.type
            else:
                # Fail if missing lineage_id
                raise ValueError(f"Missing lineage_id for item at pointer: {ptr}")
        
        # Add constraint tasks
        constraint_items = propagate_constraints(spec)
        raw_items.extend(constraint_items)
        
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
        
        # Dedupe, collapse, and canonically sort
        merged = enriched
        merged = dedupe_items(merged)
        merged = collapse_items(merged)
        final_items = canonical_sort(merged)
        
        # Assign order rank
        for it in final_items:
            it["order_rank"] = assign_order_rank(it)
        
        # Synthesize IDs with namespace
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
            # Build evaluation context
            eval_context = {
                "items": final_items,
                "spec": spec
            }
            
            # Evaluate invariant expression
            expr = invariant.get("expr", "")
            result = evaluate_invariant(expr, eval_context)
            
            # Attach result to items that match this invariant
            for item in final_items:
                item_ptr = item.get("ptr", "")
                inv_ptr = invariant.get("spec_ptr", "")
                
                if item_ptr.startswith(inv_ptr) or inv_ptr.startswith(item_ptr):
                    if "meta" not in item:
                        item["meta"] = {}
                    if "invariant_results" not in item["meta"]:
                        item["meta"]["invariant_results"] = []
                    item["meta"]["invariant_results"].append({
                        "invariant_id": invariant.get("id"),
                        "result": result
                    })
            
            # Record violations
            if not result:
                invariant_violations.append({
                    "invariant_id": invariant.get("id"),
                    "spec_ptr": invariant.get("spec_ptr"),
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
        final_items.extend(all_derived)
        
        # Attach metadata
        product_id = spec.get("metadata", {}).get("product_id", "unknown")
        decorated = []
        for it in final_items:
            decorated.append(attach_metadata(it, product_id))
        
        # Sanity check
        decorated = sanity_check(decorated)
        
        # Cross-item validation
        decorated, validation_warnings = validate_cross_item_constraints(decorated)
        
        # Group items
        grouped = group_items(decorated)
        
        # Build rollups
        rollups = build_rollups(grouped)
        
        # Write warnings
        write_warnings(product_id, validation_warnings)
        
        # Run preflight checks
        if schema is None:
            schema = {"type": "object"}  # default minimal schema
        preflight = run_preflight(spec, schema, decorated)
        
        # Enforce explicit test coverage: every checklist item must reference at least one test
        missing_tests = [it for it in decorated if not it.get("test_refs")]
        if missing_tests:
            missing_ids = [it.get("id") for it in missing_tests]
            raise RuntimeError(f"missing_test_refs: {missing_ids}")

        plan = ExecutionPlan(decorated)
        plan.stage_pass1(decorated)

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
        write_manifest(product_id, result)
        
        # Compute stability
        signature = compute_run_signature(result)
        result["stable"] = compare_to_previous(product_id, signature)
        
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
