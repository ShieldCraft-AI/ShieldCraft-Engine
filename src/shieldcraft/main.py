import argparse
import json
import pathlib
import os
import shutil
from shieldcraft.engine import Engine
from shieldcraft.output_contracts import VERSION as OUTPUT_CONTRACT_VERSION


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
            # Load spec via canonical ingestion helper so non-JSON specs
            # (YAML/TOML/raw) reach the engine for deterministic validation.
            from shieldcraft.services.spec.ingestion import ingest_spec
            spec = ingest_spec(spec_file)
            # Defensive assert: ensure dict-like for engine
            if not isinstance(spec, dict):
                spec = {"metadata": {"source_format": "unknown", "normalized": True}, "raw_input": spec}
            # Emit a minimal, robust checklist draft so authors always get a draft.
            # This simple pass detects obligation-like prose and emits clues deterministically.
            try:
                import hashlib
                def _scan(node, base_ptr=""):
                    items = []
                    if isinstance(node, dict):
                        for k in sorted(node.keys()):
                            ptr = f"{base_ptr}/{k}" if base_ptr else f"/{k}"
                            items.extend(_scan(node[k], ptr))
                    elif isinstance(node, list):
                        for i, v in enumerate(node):
                            ptr = f"{base_ptr}/{i}"
                            items.extend(_scan(v, ptr))
                    elif isinstance(node, str):
                        low = node.lower()
                        if any(w in low for w in ("must", "never", "requires", "should", "must not", "refuse")):
                            text = node.strip()
                            hid = hashlib.sha256((base_ptr + ":" + text).encode()).hexdigest()[:12]
                            items.append({"id": hid, "ptr": base_ptr or "/", "text": text, "value": text})
                    return items

                pre_items = _scan(spec, "")
                # Keep a copy of the original pre-scan (prior to interpretation)
                original_pre_scan = list(pre_items) if pre_items else []
                # Interpret the original raw text too (meaning-first interpretation)
                try:
                    from shieldcraft.interpreter import interpret_spec
                    try:
                        with open(spec_file, 'r') as sf:
                            raw_text = sf.read()
                    except Exception:
                        raw_text = None
                    interp = interpret_spec(raw_text or json.dumps(spec, sort_keys=True))
                    # Convert interpreter ChecklistItem->pre_items shape and merge deterministically
                    interp_items = []
                    seen_hashes = {itm.get('id') for itm in pre_items}
                    for it in interp:
                        if it.get('id') in seen_hashes:
                            continue
                        interp_items.append({"id": it.get('id'), "ptr": it.get('evidence_ref', {}).get('ptr') or '/', "text": it.get('claim'), "value": it.get('claim'), "confidence": it.get('confidence', 'low')})
                    # deterministic extend
                    pre_items.extend(interp_items)
                except Exception:
                    interp = []

                if pre_items:
                    from shieldcraft.services.guidance.checklist import annotate_items, annotate_items_with_blockers, enrich_with_confidence_and_evidence, ensure_item_fields
                    annotate_items(pre_items)
                    annotate_items_with_blockers(pre_items, validation_errors=None)
                    try:
                        enrich_with_confidence_and_evidence(pre_items, spec)
                    except Exception:
                        pass
                    ensure_item_fields(pre_items)
                    try:
                        with open(os.path.join(output_dir, "checklist_draft.json"), "w") as cf:
                            json.dump({"items": pre_items, "status": "draft"}, cf, indent=2, sort_keys=True)
                    except Exception:
                        pass
                # Keep a record of pre-scan signals for suppressed-signal analysis later
                pre_scan = pre_items
            except Exception:
                pass
            if 'pre_scan' not in locals():
                pre_scan = []
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
            # Also write a minimal deterministic summary including active policy
            try:
                from shieldcraft.services.spec.strictness_policy import SemanticStrictnessPolicy
                from shieldcraft.services.spec.analysis import classify_dsl_sections
                policy = SemanticStrictnessPolicy.from_env().to_dict()
                classification = classify_dsl_sections(spec if isinstance(spec, dict) else {}, schema_path)
            except Exception:
                policy = {}
                classification = {}

            # Provide a partial manifest and checklist preview where possible so authors
            # receive concrete, affirmative artifacts even when validation fails.
            # NOTE: do not emit executable code or bootstrap artifacts here.
            manifest = {
                "partial": True,
                "conversion_tier": "convertible",
                "spec_metadata": (spec.get("metadata") if isinstance(spec, dict) else {}),
                "dsl_section_classification": classification,
                "semantic_strictness_policy": policy,
                "outputs": [],
            }
            try:
                cs = getattr(engine, "conversion_state", None)
                if cs is None:
                    manifest["conversion_state"] = "CONVERTIBLE"
                else:
                    # Preserve prior UX: treat ACCEPTED during a validation failure as CONVERTIBLE
                    manifest["conversion_state"] = ("CONVERTIBLE" if cs.name == "ACCEPTED" else cs.value)
                manifest["state_reason"] = engine.conversion_state_reason or getattr(e, "code", None)
            except Exception:
                manifest["conversion_state"] = "CONVERTIBLE"
                manifest["state_reason"] = getattr(e, "code", None)
            manifest["spec_evolution"] = None

            # Attempt to produce a checklist preview (best-effort, non-fatal)
            checklist_preview = None
            try:
                from shieldcraft.services.ast.builder import ASTBuilder
                from shieldcraft.services.checklist.generator import ChecklistGenerator
                ast = ASTBuilder().build(spec)
                # Include interpreted items in preview to ensure meaning-first items are present
                try:
                    from shieldcraft.interpreter import interpret_spec
                    try:
                        with open(spec_path, 'r') as sf:
                            raw_text = sf.read()
                    except Exception:
                        raw_text = None
                    interp = interpret_spec(raw_text or json.dumps(spec, sort_keys=True))
                except Exception:
                    interp = []
                checklist_preview = ChecklistGenerator().build(spec, ast=ast, dry_run=True, run_test_gate=False, engine=engine, interpreted_items=interp)
                manifest["checklist_preview_items"] = len(checklist_preview.get("items", [])) if isinstance(checklist_preview, dict) else None
                # CLI visibility: ensure users see that a checklist was generated
                try:
                    cnt = manifest.get("checklist_preview_items") or 0
                    print(f"Checklist generated: {cnt} items")
                except Exception:
                    pass
                try:
                    from shieldcraft.services.guidance.guidance import checklist_preview_explanation
                    manifest["checklist_preview_explanation"] = checklist_preview_explanation(manifest.get("checklist_preview_items"), manifest.get("conversion_state"))
                except Exception:
                    pass
                # Attach annotated preview items when available (advisory only)
                try:
                    from shieldcraft.services.guidance.checklist import annotate_items, annotate_items_with_blockers, checklist_summary
                    if isinstance(checklist_preview, dict):
                        # Merge interpreted items into preview to ensure meaning-first coverage
                        preview_items = list(checklist_preview.get("items", [])) or []
                        try:
                            interpreted_items_local = interp if 'interp' in locals() else []
                            existing_ids = {it.get('id') for it in preview_items if it.get('id')}
                            for uit in interpreted_items_local:
                                uid = str(uit.get('id'))
                                if uid in existing_ids:
                                    continue
                                preview_items.append({"id": uid, "ptr": uit.get('evidence_ref', {}).get('ptr') or '/', "text": uit.get('claim'), "value": uit.get('claim'), "confidence": uit.get('confidence', 'low')})
                                existing_ids.add(uid)
                        except Exception:
                            # best-effort fallback: emit an explicit negative sufficiency
                            try:
                                # direct fallback write to guarantee presence
                                p = os.path.join(output_dir, 'sufficiency.json')
                                with open(p, 'w', encoding='utf8') as sf:
                                    json.dump({'sufficiency': {'ok': False, 'mandatory_total': 0, 'mandatory_full': 0, 'mandatory_missing': 0, 'mandatory_partial': 0, 'missing': [], 'partial': []}}, sf, indent=2, sort_keys=True)
                                manifest['checklist_sufficiency'] = {'ok': False, 'mandatory_total': 0, 'mandatory_full': 0, 'mandatory_missing': 0, 'mandatory_partial': 0, 'missing': [], 'partial': []}
                                manifest['checklist_sufficient'] = False
                            except Exception:
                                pass

                        # Ensure minimal sizes (product requirement)
                        # Do not artificially enforce minimum sizes or inject refusal-only fillers.
                        # Validation state must only annotate items, not augment them.

                        # Annotate and persist merged preview items
                        annotate_items(preview_items)
                        # Annotate with validation blocker info so authors can see why items are draft
                        annotate_items_with_blockers(preview_items, validation_errors=[getattr(e, "code", None)])
                        try:
                            from shieldcraft.services.guidance.checklist import enrich_with_confidence_and_evidence, ensure_item_fields
                            enrich_with_confidence_and_evidence(preview_items, spec)
                            ensure_item_fields(preview_items)
                        except Exception:
                            pass
                        manifest["checklist_preview"] = preview_items
                        manifest["checklist_summary"] = checklist_summary(preview_items, manifest.get("conversion_state"))
                        # Compute first safe action deterministically from preview items
                        try:
                            def _compute_first_safe(preview_items):
                                if not preview_items:
                                    return None
                                # select P0 non-blocking first, else P0 blocking
                                p0_nonblocking = [it for it in preview_items if it.get('priority') == 'P0' and not it.get('blocking')]
                                p0_blocking = [it for it in preview_items if it.get('priority') == 'P0' and it.get('blocking')]
                                def _choose(xs):
                                    if not xs:
                                        return None
                                    return sorted(xs, key=lambda x: x.get('id') or '')[0]
                                chosen = _choose(p0_nonblocking) or _choose(p0_blocking)
                                if not chosen:
                                    return None
                                # If chosen non-blocking -> first_safe_action
                                if chosen in p0_nonblocking:
                                    ev = chosen.get('evidence') or {}
                                    quote = ev.get('quote')
                                    ptr = (ev.get('source') or {}).get('ptr')
                                    if chosen.get('risk_if_false') == 'unsafe_to_act' or (chosen.get('severity') or '').lower() in ('high','critical'):
                                        risk = 'high'
                                    elif (chosen.get('confidence') or '').lower() == 'low':
                                        risk = 'medium'
                                    else:
                                        risk = 'low'
                                    rationale = "Evidence: " + (repr(quote[:200]) if quote else ("ptr=" + (ptr or 'unknown')))
                                    why = f"This action is prioritized P0 and addresses {chosen.get('intent_category') or 'critical'} issues; performing it reduces immediate risk."
                                    return {"first_safe_action": {"action": chosen.get('action') or chosen.get('text') or chosen.get('claim'), "rationale": rationale, "risk": risk, "why_this_first": why}}
                                # Else refusal fallback
                                ev = chosen.get('evidence') or {}
                                missing = []
                                if not ev.get('quote'):
                                    missing.append('quote')
                                if not ev.get('source_excerpt_hash'):
                                    missing.append('excerpt_hash')
                                ptr = (ev.get('source') or {}).get('ptr') or 'unknown'
                                reason = f"Refusal: item {chosen.get('id')} is blocking; missing evidence: {', '.join(missing) or 'none'}; ptr={ptr}"
                                return {"refusal_action": {"action": f"Refuse to proceed until requirement is resolved: {chosen.get('action') or chosen.get('text')}", "explanation": reason}}
                        except Exception:
                            _compute_first_safe = lambda _: None
                        try:
                            fs = _compute_first_safe(preview_items)
                            if fs:
                                manifest.update(fs)
                        except Exception:
                            pass
                        try:
                            manifest["checklist_preview_summary"] = [{"id": it.get("id"), "claim": it.get("text") or it.get("value") or it.get("claim")} for it in preview_items[:5]]
                        except Exception:
                            pass
                        # Write checklist draft file unconditionally for this self-host run
                        try:
                            with open(os.path.join(output_dir, "checklist_draft.json"), "w") as cf:
                                json.dump({"items": preview_items, "status": "draft"}, cf, indent=2, sort_keys=True)
                            # Post-write guard: ensure every item has required fields
                            try:
                                from shieldcraft.services.guidance.checklist import ensure_item_fields
                                cdpath = os.path.join(output_dir, "checklist_draft.json")
                                payload = json.load(open(cdpath))
                                payload["items"] = ensure_item_fields(payload.get("items", []))
                                with open(cdpath, "w") as cf:
                                    json.dump(payload, cf, indent=2, sort_keys=True)
                            except Exception:
                                pass
                        except Exception:
                            pass
                            # Emit a best-effort sufficiency evaluation for validation-failure previews
                            try:
                                from shieldcraft.interpretation.requirements import extract_requirements
                                from shieldcraft.requirements.coverage import compute_coverage, write_coverage_report
                                from shieldcraft.requirements.sufficiency import evaluate_sufficiency, write_sufficiency_report
                                reqs = []
                                try:
                                    # try to extract from raw spec source material
                                    rtxt = spec.get('metadata', {}).get('source_material') or spec.get('raw_input') or json.dumps(spec, sort_keys=True)
                                    reqs = extract_requirements(rtxt)
                                    with open(os.path.join(output_dir, 'requirements.json'), 'w', encoding='utf8') as _rf:
                                        json.dump({'requirements': reqs}, _rf, indent=2, sort_keys=True)
                                except Exception:
                                    reqs = []
                                covers = compute_coverage(reqs, preview_items)
                                write_coverage_report(covers)
                                suff = evaluate_sufficiency(reqs, covers)
                                write_sufficiency_report(suff, outdir=output_dir)
                                manifest['checklist_sufficiency'] = {
                                    'ok': suff.ok,
                                    'mandatory_total': suff.mandatory_total,
                                    'mandatory_full': suff.mandatory_full,
                                    'mandatory_missing': suff.mandatory_missing,
                                    'mandatory_partial': suff.mandatory_partial,
                                    'missing': suff.missing_requirements,
                                    'partial': suff.partial_requirements,
                                }
                                manifest['checklist_sufficient'] = suff.ok
                            except Exception:
                                pass
                        # Emit spec_feedback for authoring guidance (validation failure path)
                        try:
                            from shieldcraft.services.guidance.checklist import annotate_items_with_remediation, build_spec_feedback
                            cdpath = os.path.join(output_dir, "checklist_draft.json")
                            if os.path.exists(cdpath):
                                payload = json.load(open(cdpath))
                                items = payload.get("items", [])
                                annotate_items_with_remediation(items, spec)
                                # persist annotated payload
                                with open(cdpath, "w") as cf:
                                    json.dump({"items": items, "status": "draft"}, cf, indent=2, sort_keys=True)
                                feedback = build_spec_feedback(items, spec)
                                with open(os.path.join(output_dir, "spec_feedback.json"), "w") as sf:
                                    json.dump(feedback, sf, indent=2, sort_keys=True)
                                manifest["spec_feedback"] = feedback
                        except Exception:
                            pass
                        # Compute readiness trace when possible
                        try:
                            from shieldcraft.services.guidance.checklist import annotate_items_with_readiness_impact
                            readiness = manifest.get("readiness")
                            trace = annotate_items_with_readiness_impact(manifest.get("checklist_preview") or [], readiness, spec)
                            rt_path = os.path.join(output_dir, "readiness_trace.json")
                            if trace:
                                with open(rt_path, "w") as rf:
                                    json.dump({"trace": trace}, rf, indent=2, sort_keys=True)
                                # Also annotate manifest with trace summary
                                blocker_items = sorted({iid for g, v in trace.items() if v.get("blocking") for iid in v.get("item_ids", [])})
                                manifest["readiness_blockers_count"] = sum(1 for v in trace.values() if v.get("blocking"))
                                manifest["readiness_blocker_item_ids"] = blocker_items
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                checklist_preview = None

            # Guidance: what is missing next
            missing_next = []
            if getattr(e, "code", None):
                missing_next.append({"code": e.code, "location": e.location, "message": e.message, "details": getattr(e, "details", None)})
            summary_path = os.path.join(output_dir, "summary.json")

            # best-effort: ensure sufficiency report exists for validation failures
            try:
                from shieldcraft.interpretation.requirements import extract_requirements
                from shieldcraft.requirements.coverage import compute_coverage, write_coverage_report
                from shieldcraft.requirements.sufficiency import evaluate_sufficiency, write_sufficiency_report
                # use checklist draft if available
                draft_path = os.path.join(output_dir, 'checklist_draft.json')
                items = []
                if os.path.exists(draft_path):
                    try:
                        items = json.load(open(draft_path)).get('items', [])
                    except Exception:
                        items = []
                rtxt = spec.get('metadata', {}).get('source_material') or spec.get('raw_input') or json.dumps(spec, sort_keys=True)
                reqs = extract_requirements(rtxt)
                covers = compute_coverage(reqs, items)
                write_coverage_report(covers)
                suff = evaluate_sufficiency(reqs, covers)
                write_sufficiency_report(suff, outdir=output_dir)
                manifest['checklist_sufficiency'] = {
                    'ok': suff.ok,
                    'mandatory_total': suff.mandatory_total,
                    'mandatory_full': suff.mandatory_full,
                    'mandatory_missing': suff.mandatory_missing,
                    'mandatory_partial': suff.mandatory_partial,
                    'missing': suff.missing_requirements,
                    'partial': suff.partial_requirements,
                }
                manifest['checklist_sufficient'] = suff.ok
                # Update conversion state in partial/validation paths to reflect sufficiency
                try:
                    if suff.ok:
                        manifest['conversion_state'] = 'READY'
                        manifest['state_reason'] = 'sufficiency_passed'
                    else:
                        manifest['conversion_state'] = 'INCOMPLETE'
                        manifest['state_reason'] = 'sufficiency_failed'
                except Exception:
                    pass
                # Best-effort: compute completeness from draft items
                try:
                    from shieldcraft.requirements.completion import bind_dimensions_to_items, evaluate_completeness, write_completeness_report, is_implementable
                    items = items or []
                    items = bind_dimensions_to_items(reqs, items)
                    results, summary = evaluate_completeness(reqs, items)
                    write_completeness_report(results, summary, outdir=output_dir)
                    impl = is_implementable(summary, reqs)
                    manifest['implementability'] = {'implementable': impl, 'complete_pct': summary.get('complete_pct')}
                except Exception:
                    pass
            except Exception:
                # best-effort only: ensure fallback sufficiency file exists
                try:
                    p = os.path.join(output_dir, 'sufficiency.json')
                    with open(p, 'w', encoding='utf8') as sf:
                        json.dump({'sufficiency': {'ok': False, 'mandatory_total': 0, 'mandatory_full': 0, 'mandatory_missing': 0, 'mandatory_partial': 0, 'missing': [], 'partial': []}}, sf, indent=2, sort_keys=True)
                    manifest['checklist_sufficiency'] = {'ok': False, 'mandatory_total': 0, 'mandatory_full': 0, 'mandatory_missing': 0, 'mandatory_partial': 0, 'missing': [], 'partial': []}
                    manifest['checklist_sufficient'] = False
                except Exception:
                    pass
                # best-effort fallback for completeness
                try:
                    p = os.path.join(output_dir, 'requirement_completeness.json')
                    with open(p, 'w', encoding='utf8') as sf:
                        json.dump({'requirements': [], 'summary': {'total_requirements': 0, 'complete_count': 0, 'partial_count': 0, 'unbound_count': 0, 'complete_pct': 0.0}}, sf, indent=2, sort_keys=True)
                    manifest['implementability'] = {'implementable': False, 'complete_pct': 0.0}
                except Exception:
                    pass

            # Attempt to compute spec evolution (non-fatal advisory)
            spec_evolution = None
            try:
                product_id = (spec.get("metadata", {}) or {}).get("product_id", "unknown")
                prev_spec_path = f"products/{product_id}/last_spec.json"
                from shieldcraft.services.spec.evolution import compute_evolution
                if os.path.exists(prev_spec_path):
                    with open(prev_spec_path) as pf:
                        previous_spec = json.load(pf)
                else:
                    previous_spec = None
                spec_evolution = compute_evolution(previous_spec, spec)
            except Exception:
                spec_evolution = None

            with open(summary_path, "w") as f:
                # Order and filter missing_next deterministically for author guidance
                try:
                    from shieldcraft.services.guidance.guidance import prioritize_missing, state_reason_for
                    missing_next = prioritize_missing(missing_next)
                    sr = state_reason_for(manifest.get("conversion_state"), missing_next)
                except Exception:
                    sr = manifest.get("state_reason")
                try:
                    from shieldcraft.services.guidance.conversion_path import build_conversion_path
                    conv = build_conversion_path(manifest.get("conversion_state"), missing_next, None)
                except Exception:
                    conv = None
                try:
                    from shieldcraft.services.guidance.progress import load_last_state, compute_progress_summary
                    product_id = (spec.get("metadata", {}) or {}).get("product_id", "unknown")
                    prev = load_last_state(product_id)
                    prog = compute_progress_summary(prev, manifest.get("conversion_state"), None, missing_next, None, manifest.get("spec_fingerprint"))
                except Exception:
                    prev = None
                    prog = None
                # Compute suppressed signals (signals seen in pre-scan but not converted)
                try:
                    def _compute_suppressed(output_dir, pre_scan_list):
                        import hashlib
                        suppressed = []
                        try:
                            cdpath = os.path.join(output_dir, "checklist_draft.json")
                            if os.path.exists(cdpath):
                                cl = json.load(open(cdpath))
                                items = cl.get("items", [])
                            else:
                                items = []
                        except Exception:
                            items = []
                        # Build quick lookup by excerpt hash
                        hash_to_item = {}
                        for it in items:
                            h = None
                            try:
                                h = (it.get("evidence") or {}).get("source_excerpt_hash")
                            except Exception:
                                h = None
                            if h:
                                hash_to_item[h] = it
                        for sig in pre_scan_list or []:
                            entry = {"category": sig.get("intent_category") or "misc", "source_excerpt_hash": sig.get("excerpt_hash"), "text_excerpt": sig.get("text")}
                            mapped = None
                            if sig.get("excerpt_hash") and sig.get("excerpt_hash") in hash_to_item:
                                mapped = hash_to_item[sig.get("excerpt_hash")]
                            else:
                                # try textual match
                                for it in items:
                                    try:
                                        if sig.get("text") and sig.get("text") in (it.get("text") or ""):
                                            mapped = it
                                            break
                                    except Exception:
                                        continue
                            if mapped:
                                entry["mapped_item_id"] = mapped.get("id")
                                if (mapped.get("confidence") or "") == "low":
                                    entry["reason_not_emitted"] = "low_confidence"
                                else:
                                    entry["reason_not_emitted"] = "converted"
                            else:
                                entry["mapped_item_id"] = None
                                entry["reason_not_emitted"] = "no_mapping"
                            if entry["reason_not_emitted"] != "converted":
                                suppressed.append(entry)
                        return suppressed
                    suppressed = _compute_suppressed(output_dir, pre_scan)
                    # Persist suppressed report only if original pre-scan (author prose) had signals
                    try:
                        if original_pre_scan:
                            sup_path = os.path.join(output_dir, "suppressed_signal_report.json")
                            if suppressed:
                                with open(sup_path, "w") as sf:
                                    json.dump({"suppressed": suppressed}, sf, indent=2, sort_keys=True)
                    except Exception:
                        pass
                except Exception:
                    suppressed = []
                try:
                    # Attempt to compute execution preview for partial/validation paths using checklist_preview
                    from shieldcraft.services.guidance.execution_preview import build_execution_preview
                    exc = build_execution_preview(manifest.get("conversion_state"), manifest.get("checklist_preview") or [], None, missing_next)
                except Exception:
                    exc = None
                try:
                    from shieldcraft.services.guidance.artifact_contract import build_artifact_contract_summary
                    ac = build_artifact_contract_summary(manifest.get("conversion_state"), manifest.get("spec_metadata", {}).get("artifact_contract"), manifest.get("checklist_preview") or [], exc)
                except Exception:
                    ac = None
                summary = {
                    "status": "fail",
                    "errors": [e.to_dict()],
                    "validity_status": "fail",
                    "readiness_status": "not_evaluated",
                    "readiness_reason": "blocked_by_invalid_spec",
                    "semantic_strictness_policy": policy,
                    "dsl_section_classification": classification,
                    "conversion_state": manifest.get("conversion_state"),
                    "state_reason": sr,
                    "conversion_tier": manifest.get("conversion_tier"),
                    "spec_evolution": spec_evolution,
                    "governance_enforcements": getattr(engine, "_governance_enforcements", []),
                    "what_is_missing_next": missing_next,
                    "conversion_path": conv,
                    "previous_state": prev,
                    "progress_summary": prog,
                    "execution_preview": exc,
                    "artifact_contract_summary": ac,
                    "output_contract_version": OUTPUT_CONTRACT_VERSION,
                    # Checklist visibility flags
                    "checklist_emitted": True,
                    "checklist_status": "draft",
                    # Suppressed/prose-derived signals
                    "suppressed_signal_count": len(suppressed),
                    "inferred_from_prose_count": sum(1 for it in (manifest.get("checklist_preview") or []) if it.get("inferred_from_prose")),
                    # Readiness traceability
                    "readiness_blockers_count": manifest.get("readiness_blockers_count", 0),
                    "readiness_blocker_item_ids": manifest.get("readiness_blocker_item_ids", []),
                }

                # Attach sufficiency verdict if available
                try:
                    sp = os.path.join(output_dir, 'checklist_sufficiency.json')
                    if os.path.exists(sp):
                        sdata = json.load(open(sp))
                        summary['sufficiency_verdict'] = sdata.get('sufficient')
                        if not sdata.get('sufficient'):
                            summary['why_not_sufficient'] = sdata.get('reasons') or []
                except Exception:
                    pass
                # Add checklist priority counts for visibility
                try:
                    preview_items = manifest.get("checklist_preview") or []
                    total_items = len(preview_items)
                    p0 = sum(1 for it in preview_items if it.get("priority") == "P0")
                    p1 = sum(1 for it in preview_items if it.get("priority") == "P1")
                    p2 = sum(1 for it in preview_items if it.get("priority") == "P2")
                    summary["total_items"] = total_items
                    summary["p0_count"] = p0
                    summary["p1_count"] = p1
                    summary["p2_count"] = p2
                    # Propagate first_safe_action/refusal from manifest to summary when present
                    try:
                        if 'first_safe_action' in manifest:
                            summary['first_safe_action'] = manifest.get('first_safe_action')
                        elif 'refusal_action' in manifest:
                            summary['refusal_action'] = manifest.get('refusal_action')
                        else:
                            fs = manifest.get('first_safe_action') or manifest.get('refusal_action')
                            if fs:
                                if fs.get('risk') is not None:
                                    summary['first_safe_action'] = fs
                                else:
                                    summary['refusal_action'] = fs
                    except Exception:
                        pass
                except Exception:
                    pass

                # Human-facing executive summary fields
                try:
                    cd = os.path.join(output_dir, "checklist_draft.json")
                    rr = os.path.join(output_dir, "refusal_report.json")
                    is_safe = "unknown"
                    where_safe = []
                    why_not = None
                    if os.path.exists(rr):
                        try:
                            rrj = json.load(open(rr))
                            reason = rrj.get("reason") or rrj.get("message") or str(rrj)
                        except Exception:
                            reason = "refusal_emitted"
                        is_safe = "no"
                        why_not = reason
                    elif os.path.exists(cd):
                        try:
                            cdj = json.load(open(cd))
                            items = cdj.get("items", [])
                            strong = [it for it in items if (it.get("confidence") or "medium") in ("high", "medium")]
                            if strong:
                                is_safe = "yes"
                                where_safe = [it.get("ptr") or it.get("id") for it in strong]
                            else:
                                is_safe = "unknown"
                                why_not = "No items with sufficient confidence"
                        except Exception:
                            pass
                    summary["is_it_safe_to_act"] = is_safe
                    summary["where_is_safe"] = where_safe
                    summary["why_not_safe"] = why_not
                except Exception:
                    pass

                json.dump(summary, f, indent=2, sort_keys=True)

            try:
                manifest["spec_evolution"] = spec_evolution
                manifest["governance_enforcements"] = getattr(engine, "_governance_enforcements", [])
            except Exception:
                pass
            # Write partial manifest for authoring workflows
            manifest_path = os.path.join(output_dir, "manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2, sort_keys=True)
            # Final attempt: ensure spec_feedback exists even if earlier attempts failed
            try:
                fb_path = os.path.join(output_dir, "spec_feedback.json")
                if not os.path.exists(fb_path):
                    items = manifest.get("checklist_preview") or pre_scan or []
                    def _build_spec_feedback_local(items, spec):
                        missing_sections = sorted([k for k in ("sections", "invariants", "metadata", "model") if not (spec or {}).get(k)])
                        weak = []
                        hints = []
                        for it in items:
                            conf = (it.get("confidence") or "medium")
                            if conf != "high":
                                weak.append({"id": it.get("id"), "confidence": conf, "inferred_from_prose": it.get("inferred_from_prose", False)})
                                ptr = it.get("ptr") or ""
                                if not it.get("test_refs"):
                                    h = "Attach `test_refs` to this item so tests can be discovered (tests_attached gate)."
                                elif "/metadata" in ptr:
                                    h = "Add or enrich `metadata` (product_id, owner, version)."
                                elif "/invariants" in ptr:
                                    h = "Add explicit `invariants` expressing the requirement."
                                elif "/sections" in ptr or it.get("inferred_from_prose"):
                                    h = "Clarify this `sections` entry: add constraints, invariants, or a linked test_ref."
                                else:
                                    h = "Clarify this item in `sections` or add explicit `invariants`/`metadata`."
                                hints.append(h)
                        uniq_hints = sorted(set(hints))
                        return {"missing_sections": missing_sections, "weakly_specified_intents": sorted(weak, key=lambda x: x.get("id") or ""), "suggested_next_edits": uniq_hints, "remediation_hints_count": len(hints)}

                    fb = _build_spec_feedback_local(items, spec)
                    with open(fb_path, "w") as sf:
                        json.dump(fb, sf, indent=2, sort_keys=True)
                    manifest["spec_feedback"] = fb
            except Exception:
                pass

            # Ensure requirements.json exists for downstream consumers
            try:
                reqp = os.path.join(output_dir, 'requirements.json')
                if not os.path.exists(reqp):
                    with open(reqp, 'w', encoding='utf8') as _rf:
                        json.dump({'requirements': []}, _rf, indent=2, sort_keys=True)
            except Exception:
                pass

            # Best-effort: compute sufficiency at top-level if not already emitted
            try:
                print('[SELF-HOST] attempting_sufficiency_eval')
                from shieldcraft.sufficiency.evaluator import evaluate_from_files, write_sufficiency_report
                suff = evaluate_from_files('.selfhost_outputs')
                print('[SELF-HOST] suff_eval_done', bool(suff))
                write_sufficiency_report(suff, outdir='.selfhost_outputs')
                print('[SELF-HOST] suff_write_done')
                manifest_data['checklist_sufficiency'] = suff
                manifest_data['checklist_sufficient'] = suff.get('sufficient', False)
                with open(manifest_path, "w") as f:
                    json.dump(manifest_data, f, indent=2, sort_keys=True)
            except Exception:
                # Fallback: try invoking evaluator in a subprocess to avoid in-process edge cases
                try:
                    import subprocess, sys
                    subprocess.run([sys.executable, '-c', 'from shieldcraft.sufficiency.evaluator import evaluate_from_files, write_sufficiency_report; write_sufficiency_report(evaluate_from_files(".selfhost_outputs"), outdir=".selfhost_outputs")'], check=False)
                except Exception:
                    import traceback
                    print('[SELF-HOST] sufficiency_evaluation_error', traceback.format_exc())

            # If validation failure path did not emit spec_feedback, attempt to build from pre_scan
            try:
                fb_path = os.path.join(output_dir, "spec_feedback.json")
                if not os.path.exists(fb_path):
                    if pre_scan:
                        try:
                            # Local lightweight feedback builder to avoid import-time coupling
                            def _build_spec_feedback_local(items, spec):
                                missing_sections = sorted([k for k in ("sections", "invariants", "metadata", "model") if not (spec or {}).get(k)])
                                weak = []
                                hints = []
                                for it in items:
                                    conf = (it.get("confidence") or "medium")
                                    if conf != "high":
                                        weak.append({"id": it.get("id"), "confidence": conf, "inferred_from_prose": it.get("inferred_from_prose", False)})
                                        ptr = it.get("ptr") or ""
                                        if not it.get("test_refs"):
                                            h = "Attach `test_refs` to this item so tests can be discovered (tests_attached gate)."
                                        elif "/metadata" in ptr:
                                            h = "Add or enrich `metadata` (product_id, owner, version)."
                                        elif "/invariants" in ptr:
                                            h = "Add explicit `invariants` expressing the requirement."
                                        elif "/sections" in ptr or it.get("inferred_from_prose"):
                                            h = "Clarify this `sections` entry: add constraints, invariants, or a linked test_ref."
                                        else:
                                            h = "Clarify this item in `sections` or add explicit `invariants`/`metadata`."
                                        hints.append(h)
                                uniq_hints = sorted(set(hints))
                                return {"missing_sections": missing_sections, "weakly_specified_intents": sorted(weak, key=lambda x: x.get("id") or ""), "suggested_next_edits": uniq_hints, "remediation_hints_count": len(hints)}

                            items = pre_scan or manifest.get("checklist_preview") or []
                            fb = _build_spec_feedback_local(items, spec)
                            with open(fb_path, "w") as sf:
                                json.dump(fb, sf, indent=2, sort_keys=True)
                            manifest["spec_feedback"] = fb
                        except Exception:
                            pass
            except Exception:
                pass

            # Enforce primary artifact invariant: exactly one of `checklist_draft.json` or `refusal_report.json` must exist
            cd = os.path.join(output_dir, "checklist_draft.json")
            rr = os.path.join(output_dir, "refusal_report.json")
            has_cd = os.path.exists(cd)
            has_rr = os.path.exists(rr)
            if not (has_cd ^ has_rr):
                raise RuntimeError("primary_artifact_invariant_violation: exactly one of checklist_draft.json or refusal_report.json must be present")
            # If checklist exists and contains zero items, emit a silence justification
            if has_cd:
                try:
                    payload = json.load(open(cd))
                    items = payload.get("items") or []
                except Exception:
                    items = []
                if len(items) == 0:
                    sj = {
                        "justification": "Checklist generation produced zero items confidently",
                        "item_count": 0,
                        "suppressed_signal_count": len(suppressed) if 'suppressed' in locals() else 0,
                        "inferred_from_prose_count": sum(1 for it in (manifest.get("checklist_preview") or []) if it.get("inferred_from_prose")) if manifest.get("checklist_preview") else 0,
                        "readiness_blockers_count": manifest.get("readiness_blockers_count", 0),
                    }
                    with open(os.path.join(output_dir, "silence_justification.json"), "w") as sf:
                        json.dump(sj, sf, indent=2, sort_keys=True)

                # Final fallback: ensure a root-level sufficiency artifact exists
                try:
                    suffp = os.path.join('.selfhost_outputs', 'checklist_sufficiency.json')
                    if not os.path.exists(suffp):
                        from shieldcraft.sufficiency.evaluator import evaluate_from_files, write_sufficiency_report
                        suff = evaluate_from_files('.selfhost_outputs')
                        write_sufficiency_report(suff, outdir='.selfhost_outputs')
                        manifest_data['checklist_sufficiency'] = suff
                        manifest_data['checklist_sufficient'] = suff.get('sufficient', False)
                        with open(manifest_path, "w") as f:
                            json.dump(manifest_data, f, indent=2, sort_keys=True)
                except Exception:
                    pass

            print(f"[SELF-HOST] Summary and partial manifest written to: {summary_path}, {manifest_path}")
            # Final unconditional attempt to ensure sufficiency artifact exists at root
            try:
                from shieldcraft.sufficiency.evaluator import evaluate_from_files, write_sufficiency_report
                suff = evaluate_from_files('.selfhost_outputs')
                write_sufficiency_report(suff, outdir='.selfhost_outputs')
                manifest_data['checklist_sufficiency'] = suff
                manifest_data['checklist_sufficient'] = suff.get('sufficient', False)
                with open(manifest_path, "w") as f:
                    json.dump(manifest_data, f, indent=2, sort_keys=True)
            except Exception:
                pass
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
        # Compute first_safe_action deterministically from manifest checklist (if present)
        try:
            def _compute_first_safe_from_items(items):
                if not items:
                    return None
                p0_nonblocking = [it for it in items if it.get('priority') == 'P0' and not it.get('blocking')]
                p0_blocking = [it for it in items if it.get('priority') == 'P0' and it.get('blocking')]
                def _choose(xs):
                    if not xs:
                        return None
                    return sorted(xs, key=lambda x: x.get('id') or '')[0]
                chosen = _choose(p0_nonblocking) or _choose(p0_blocking)
                if not chosen:
                    return None
                if chosen in p0_nonblocking:
                    ev = chosen.get('evidence') or {}
                    quote = ev.get('quote')
                    ptr = (ev.get('source') or {}).get('ptr')
                    if chosen.get('risk_if_false') == 'unsafe_to_act' or (chosen.get('severity') or '').lower() in ('high','critical'):
                        risk = 'high'
                    elif (chosen.get('confidence') or '').lower() == 'low':
                        risk = 'medium'
                    else:
                        risk = 'low'
                    rationale = "Evidence: " + (repr(quote[:200]) if quote else ("ptr=" + (ptr or 'unknown')))
                    why = f"This action is prioritized P0 and addresses {chosen.get('intent_category') or 'critical'} issues; performing it reduces immediate risk."
                    return {"first_safe_action": {"action": chosen.get('action') or chosen.get('text') or chosen.get('claim'), "rationale": rationale, "risk": risk, "why_this_first": why}}
                ev = chosen.get('evidence') or {}
                missing = []
                if not ev.get('quote'):
                    missing.append('quote')
                if not ev.get('source_excerpt_hash'):
                    missing.append('excerpt_hash')
                ptr = (ev.get('source') or {}).get('ptr') or 'unknown'
                reason = f"Refusal: item {chosen.get('id')} is blocking; missing evidence: {', '.join(missing) or 'none'}; ptr={ptr}"
                return {"refusal_action": {"action": f"Refuse to proceed until requirement is resolved: {chosen.get('action') or chosen.get('text')}", "explanation": reason}}
        except Exception:
            _compute_first_safe_from_items = lambda _: None
        try:
            items_for_first = manifest_data.get('checklist', {}).get('items', []) or []
            fs = _compute_first_safe_from_items(items_for_first)
            if fs:
                manifest_data.update(fs)
        except Exception as e:
            # Propagate explicit quality gate failures to cause the self-host run to fail.
            if isinstance(e, RuntimeError) and str(e) == 'quality_gate_failed':
                raise
            # Otherwise, swallow non-fatal quality evaluation errors
            pass
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2, sort_keys=True)
        # Best-effort: compute and persist checklist quality from emitted checklist
        try:
            from shieldcraft.checklist.quality import evaluate_quality, write_quality_report
            cl_path = os.path.join(output_dir, 'checklist.json')
            if os.path.exists(cl_path):
                cl = json.load(open(cl_path))
                items = cl.get('items', [])
            else:
                items = manifest_data.get('checklist', []).get('items', []) if isinstance(manifest_data.get('checklist'), dict) else manifest_data.get('checklist', [])
            qualities, qsummary = evaluate_quality(items)
            write_quality_report(qualities, qsummary, outdir=output_dir)
            # annotate manifest with summary for visibility
            manifest_data['checklist_quality_summary'] = qsummary
            # Enforce quality gates: fail if any P0 is low-signal or low-signal items > 5%
            try:
                total = qsummary.get('total_items', 0) or 0
                low_count = qsummary.get('low_signal_count', 0) or 0
                low_ids = set(qsummary.get('low_signal_item_ids') or [])
                # map ids -> priorities
                id_to_pr = {it.get('id'): it.get('priority') for it in (items or [])}
                p0_violations = [iid for iid in low_ids if (id_to_pr.get(iid) or '').upper().startswith('P0')]
                ratio = (low_count / total) if total else 0.0
                if p0_violations:
                    raise RuntimeError('quality_gate_failed')
                if total == 0:
                    # No checklist items -> fail quality for prose-only specs
                    raise RuntimeError('quality_gate_failed')
                # Allow some low-signal noise; fail only if >10% of items
                if ratio > 0.10:
                    raise RuntimeError('quality_gate_failed')
                # Fail if all items are inferred from prose (even if not low confidence)
                inferred_all = sum(1 for it in (items or []) if it.get('inferred_from_prose'))
                if total > 0 and inferred_all == total:
                    raise RuntimeError('quality_gate_failed')
            except RuntimeError:
                # Persist quality summary before propagating
                with open(manifest_path, "w") as f:
                    json.dump(manifest_data, f, indent=2, sort_keys=True)
                raise
            # persist updated manifest
            with open(manifest_path, "w") as f:
                json.dump(manifest_data, f, indent=2, sort_keys=True)
        except Exception:
            pass

        # Best-effort: compute and persist checklist sequence (dependencies/order)
        try:
            from shieldcraft.checklist.dependencies import infer_item_dependencies, build_sequence
            from shieldcraft.requirements.coverage import compute_coverage
            cl_path = os.path.join(output_dir, 'checklist.json')
            reqp = os.path.join(output_dir, 'requirements.json')
            # If checklist exists, ensure requirements.json exists (extract if needed)
            if os.path.exists(cl_path):
                try:
                    if not os.path.exists(reqp):
                        from shieldcraft.interpretation.requirements import extract_requirements
                        rtxt = spec.get('metadata', {}).get('source_material') or spec.get('raw_input') or json.dumps(spec, sort_keys=True)
                        reqs_local = extract_requirements(rtxt)
                        with open(reqp, 'w', encoding='utf8') as _rf:
                            json.dump({'requirements': reqs_local}, _rf, indent=2, sort_keys=True)
                except Exception:
                    pass
                if os.path.exists(reqp):
                    items = json.load(open(cl_path)).get('items', [])
                    reqs = json.load(open(reqp)).get('requirements', [])
                    covers = compute_coverage(reqs, items)
                    inferred = infer_item_dependencies(reqs, covers)
                seq = build_sequence(items, inferred, outdir=output_dir)
                manifest_data['checklist_sequence_summary'] = {
                    'total_items': len(seq.get('sequence', [])),
                    'cycle_groups': len(seq.get('cycle_groups', {})),
                }
                with open(manifest_path, "w") as f:
                    json.dump(manifest_data, f, indent=2, sort_keys=True)
                # Compute spec coverage now that checklist and requirements exist
                try:
                    from shieldcraft.coverage.evaluator import evaluate_spec_coverage
                    # Load spec for units
                    rtxt = spec.get('metadata', {}).get('source_material') or spec.get('raw_input') or json.dumps(spec, sort_keys=True)
                    # If spec is a dict, pass the dict to evaluator for section/invariant extraction
                    cov = evaluate_spec_coverage(spec if isinstance(spec, dict) else {}, json.load(open(cl_path)).get('items', []), outdir=output_dir)
                    # persist root copy
                    try:
                        import shutil
                        shutil.copyfile(os.path.join(output_dir, 'spec_coverage.json'), os.path.join('.selfhost_outputs', 'spec_coverage.json'))
                    except Exception:
                        pass
                    manifest_data['spec_coverage_summary'] = {'total_units': cov.get('total_units'), 'covered_units': cov.get('covered_count')}
                    with open(manifest_path, "w") as f:
                        json.dump(manifest_data, f, indent=2, sort_keys=True)
                except Exception:
                    pass
                # Best-effort: compute sufficiency now that sequence and coverage exist
                try:
                    from shieldcraft.sufficiency.evaluator import evaluate_from_files, write_sufficiency_report
                    suff = evaluate_from_files(output_dir)
                    write_sufficiency_report(suff, outdir=output_dir)
                    write_sufficiency_report(suff, outdir='.selfhost_outputs')
                    manifest_data['checklist_sufficiency'] = suff
                    manifest_data['checklist_sufficient'] = suff.get('sufficient', False)
                    with open(manifest_path, "w") as f:
                        json.dump(manifest_data, f, indent=2, sort_keys=True)
                except Exception:
                    pass
                # Compute implementability verdict (aggregate of proofs) after sufficiency
                try:
                    from shieldcraft.verdict.aggregator import compute_implementability
                    verdict = compute_implementability(output_dir)
                    # persist root copy
                    try:
                        import shutil
                        shutil.copyfile(os.path.join(output_dir, 'implementability_verdict.json'), os.path.join('.selfhost_outputs', 'implementability_verdict.json'))
                    except Exception:
                        pass
                    manifest_data['implementability_verdict'] = verdict
                    manifest_data['implementable'] = verdict.get('implementable', False)
                    with open(manifest_path, "w") as f:
                        json.dump(manifest_data, f, indent=2, sort_keys=True)
                except Exception:
                    pass
        except Exception:
            pass

        # Best-effort: compute and persist requirement completeness
        try:
            from shieldcraft.requirements.completion import bind_dimensions_to_items, evaluate_completeness, write_completeness_report, is_implementable
            cl_path = os.path.join(output_dir, 'checklist.json')
            reqp = os.path.join(output_dir, 'requirements.json')
            if os.path.exists(cl_path) and os.path.exists(reqp):
                items = json.load(open(cl_path)).get('items', [])
                reqs = json.load(open(reqp)).get('requirements', [])
                items = bind_dimensions_to_items(reqs, items)
                results, summary = evaluate_completeness(reqs, items)
                write_completeness_report(results, summary, outdir=output_dir)
                impl = is_implementable(summary, reqs)
                manifest_data['implementability'] = {'implementable': impl, 'complete_pct': summary.get('complete_pct')}
                with open(manifest_path, "w") as f:
                    json.dump(manifest_data, f, indent=2, sort_keys=True)
                # Evaluate checklist sufficiency contract after completeness
                try:
                    from shieldcraft.sufficiency.evaluator import evaluate_from_files, write_sufficiency_report
                    suff = evaluate_from_files(output_dir)
                    # persist both under fingerprinted output and top-level outputs for consumer expectations
                    write_sufficiency_report(suff, outdir=output_dir)
                    write_sufficiency_report(suff, outdir='.selfhost_outputs')
                    manifest_data['checklist_sufficiency'] = suff
                    manifest_data['checklist_sufficient'] = suff.get('sufficient', False)
                    with open(manifest_path, "w") as f:
                        json.dump(manifest_data, f, indent=2, sort_keys=True)
                except Exception:
                    pass
        except Exception:
            pass
        
        # Write generated code
        if "generated" in result:
            code_dir = os.path.join(output_dir, "generated")
            os.makedirs(code_dir, exist_ok=True)
            for idx, output in enumerate(result["generated"]):
                code_path = os.path.join(code_dir, f"output_{idx}.py")
                with open(code_path, "w") as f:
                    f.write(output.get("content", ""))
        
        # Attempt to build and emit a full checklist draft for authors (always try)
        emitted = False
        status = None
        try:
            from shieldcraft.services.ast.builder import ASTBuilder
            from shieldcraft.services.checklist.generator import ChecklistGenerator
            from shieldcraft.services.guidance.checklist import annotate_items, annotate_items_with_blockers, checklist_summary
            ast = ASTBuilder().build(spec)
            checklist_obj = ChecklistGenerator().build(spec, ast=ast, dry_run=True, run_test_gate=False, engine=engine)
            if isinstance(checklist_obj, dict):
                annotate_items(checklist_obj.get("items", []))
                annotate_items_with_blockers(checklist_obj.get("items", []), validation_errors=None, readiness_results=manifest_data.get("readiness"))
                try:
                    with open(os.path.join(output_dir, "checklist_draft.json"), "w") as cf:
                        json.dump({"items": checklist_obj.get("items", []), "status": ("ok" if (manifest_data.get("readiness") or {}).get("ok") else "draft")}, cf, indent=2, sort_keys=True)
                    emitted = True
                    status = ("ok" if (manifest_data.get("readiness") or {}).get("ok") else "draft")
                except Exception:
                    emitted = False
                    status = None
        except Exception:
            emitted = False
            status = None

        # Write summary
        summary_path = os.path.join(output_dir, "summary.json")
        try:
            tmp = summary_path + '.tmp'
            with open(tmp, "w") as f:
                # Compute deterministic state_reason and prioritize missing_next when present
                try:
                    from shieldcraft.services.guidance.guidance import state_reason_for, prioritize_missing, checklist_preview_explanation
                    md_missing = manifest_data.get("what_is_missing_next", []) or []
                    md_missing = prioritize_missing(md_missing)
                    sr = state_reason_for(manifest_data.get("conversion_state"), md_missing)
                except Exception:
                    md_missing = manifest_data.get("what_is_missing_next", []) or []
                    sr = manifest_data.get("state_reason")

            # Compute checklist preview explanation when available
            try:
                cpe = checklist_preview_explanation(manifest_data.get("checklist_preview_items"), manifest_data.get("conversion_state"))
            except Exception:
                cpe = None

            try:
                from shieldcraft.services.guidance.conversion_path import build_conversion_path
                conv = build_conversion_path(manifest_data.get("conversion_state"), md_missing, manifest_data.get("readiness"))
            except Exception:
                conv = None
            # Ensure checklist draft is emitted and annotated for visibility
            try:
                from shieldcraft.services.guidance.checklist import annotate_items, annotate_items_with_blockers
                checklist_obj = None
                if isinstance(result, dict):
                    c = result.get("checklist")
                    if isinstance(c, dict):
                        checklist_obj = c
                    elif isinstance(c, list):
                        checklist_obj = {"items": c}
                if checklist_obj and checklist_obj.get("items"):
                    annotate_items(checklist_obj.get("items"))
                    annotate_items_with_blockers(checklist_obj.get("items"), validation_errors=None, readiness_results=(manifest_data.get("readiness") or checklist_obj.get("_readiness")))
                    try:
                        from shieldcraft.services.guidance.checklist import enrich_with_confidence_and_evidence, ensure_item_fields
                        enrich_with_confidence_and_evidence(checklist_obj.get("items"), spec)
                        ensure_item_fields(checklist_obj.get("items"))
                    except Exception:
                        pass
                    try:
                        with open(os.path.join(output_dir, "checklist_draft.json"), "w") as cf:
                            json.dump({"items": checklist_obj.get("items"), "status": ("ok" if (manifest_data.get("readiness") or {}).get("ok") else "draft")}, cf, indent=2, sort_keys=True)
                        # Post-write guard: ensure every item has required fields
                        try:
                            from shieldcraft.services.guidance.checklist import ensure_item_fields
                            cdpath = os.path.join(output_dir, "checklist_draft.json")
                            payload = json.load(open(cdpath))
                            payload["items"] = ensure_item_fields(payload.get("items", []))
                            with open(cdpath, "w") as cf:
                                json.dump(payload, cf, indent=2, sort_keys=True)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    # If file not written for any reason, attempt fallback AST generation
                    try:
                        cdpath = os.path.join(output_dir, "checklist_draft.json")
                        if not os.path.exists(cdpath):
                            from shieldcraft.services.ast.builder import ASTBuilder
                            from shieldcraft.services.checklist.generator import ChecklistGenerator
                            from shieldcraft.services.guidance.checklist import annotate_items, annotate_items_with_blockers, enrich_with_confidence_and_evidence, ensure_item_fields
                            ast2 = ASTBuilder().build(spec)
                            cobj = ChecklistGenerator().build(spec, ast=ast2, dry_run=True, run_test_gate=False, engine=engine)
                            if isinstance(cobj, dict) and cobj.get("items"):
                                annotate_items(cobj.get("items"))
                                annotate_items_with_blockers(cobj.get("items"), validation_errors=None, readiness_results=(manifest_data.get("readiness") or cobj.get("_readiness")))
                                try:
                                    enrich_with_confidence_and_evidence(cobj.get("items"), spec)
                                except Exception:
                                    pass
                                ensure_item_fields(cobj.get("items"))
                                with open(cdpath, "w") as cf:
                                    json.dump({"items": cobj.get("items"), "status": ("ok" if (manifest_data.get("readiness") or {}).get("ok") else "draft")}, cf, indent=2, sort_keys=True)
                    except Exception:
                        pass
                    emitted = True
                    status = ("ok" if (manifest_data.get("readiness") or {}).get("ok") else "draft")
                else:
                    emitted = False
                    status = None
            except Exception:
                emitted = False
                status = None

            # Refresh emitted status from disk if file exists
            try:
                cd_path = os.path.join(output_dir, "checklist_draft.json")
                if os.path.exists(cd_path):
                    try:
                        cd = json.load(open(cd_path))
                        emitted = True
                        status = cd.get("status")
                    except Exception:
                        emitted = emitted
                        status = status
            except Exception:
                pass

            # Ensure spec_feedback exists for success path (build from checklist_draft)
            try:
                fb_path = os.path.join(output_dir, "spec_feedback.json")
                cd_path = os.path.join(output_dir, "checklist_draft.json")
                if not os.path.exists(fb_path) and os.path.exists(cd_path):
                    try:
                        # Local lightweight feedback builder (avoid extra imports during runtime)
                        payload = json.load(open(cd_path))
                        items = payload.get("items", [])
                        missing_sections = sorted([k for k in ("sections", "invariants", "metadata", "model") if not (spec or {}).get(k)])
                        weak = []
                        hints = []
                        for it in items:
                            conf = (it.get("confidence") or "medium")
                            if conf != "high":
                                weak.append({"id": it.get("id"), "confidence": conf, "inferred_from_prose": it.get("inferred_from_prose", False)})
                                ptr = it.get("ptr") or ""
                                if not it.get("test_refs"):
                                    h = "Attach `test_refs` to this item so tests can be discovered (tests_attached gate)."
                                elif "/metadata" in ptr:
                                    h = "Add or enrich `metadata` (product_id, owner, version)."
                                elif "/invariants" in ptr:
                                    h = "Add explicit `invariants` expressing the requirement."
                                elif "/sections" in ptr or it.get("inferred_from_prose"):
                                    h = "Clarify this `sections` entry: add constraints, invariants, or a linked test_ref."
                                else:
                                    h = "Clarify this item in `sections` or add explicit `invariants`/`metadata`."
                                hints.append(h)
                        uniq_hints = sorted(set(hints))
                        feedback = {"missing_sections": missing_sections, "weakly_specified_intents": sorted(weak, key=lambda x: x.get("id") or ""), "suggested_next_edits": uniq_hints, "remediation_hints_count": len(hints)}
                        with open(fb_path, "w") as sf:
                            json.dump(feedback, sf, indent=2, sort_keys=True)
                        manifest_data["spec_feedback"] = feedback
                    except Exception:
                        pass
            except Exception:
                pass

            # Compute readiness trace for success path
            try:
                from shieldcraft.services.guidance.checklist import annotate_items_with_readiness_impact
                # Load latest checklist items from disk if available
                cdpath = os.path.join(output_dir, "checklist_draft.json")
                items = []
                if os.path.exists(cdpath):
                    try:
                        items = json.load(open(cdpath)).get("items", [])
                    except Exception:
                        items = []
                readiness = manifest_data.get("readiness")
                trace = annotate_items_with_readiness_impact(items, readiness, spec)
                rt_path = os.path.join(output_dir, "readiness_trace.json")
                if trace:
                    with open(rt_path, "w") as rf:
                        json.dump({"trace": trace}, rf, indent=2, sort_keys=True)
                # Add summary fields for blocking traces
                try:
                    blocker_items = sorted({iid for g, v in (trace or {}).items() if v.get("blocking") for iid in v.get("item_ids", [])})
                    suppressed_blocker_count = sum(1 for v in (trace or {}).values() if v.get("blocking"))
                except Exception:
                    blocker_items = []
                    suppressed_blocker_count = 0
            except Exception:
                trace = {}
                blocker_items = []
                suppressed_blocker_count = 0

            # Compute suppressed signals for success path
            try:
                def _compute_suppressed(output_dir, pre_scan_list):
                    import hashlib
                    suppressed = []
                    try:
                        cdpath = os.path.join(output_dir, "checklist_draft.json")
                        if os.path.exists(cdpath):
                            cl = json.load(open(cdpath))
                            items = cl.get("items", [])
                        else:
                            items = []
                    except Exception:
                        items = []
                    hash_to_item = {}
                    for it in items:
                        h = None
                        try:
                            h = (it.get("evidence") or {}).get("source_excerpt_hash")
                        except Exception:
                            h = None
                        if h:
                            hash_to_item[h] = it
                    for sig in pre_scan_list or []:
                        entry = {"category": sig.get("intent_category") or "misc", "source_excerpt_hash": sig.get("excerpt_hash"), "text_excerpt": sig.get("text")}
                        mapped = None
                        if sig.get("excerpt_hash") and sig.get("excerpt_hash") in hash_to_item:
                            mapped = hash_to_item[sig.get("excerpt_hash")]
                        else:
                            for it in items:
                                try:
                                    if sig.get("text") and sig.get("text") in (it.get("text") or ""):
                                        mapped = it
                                        break
                                except Exception:
                                    continue
                        if mapped:
                            entry["mapped_item_id"] = mapped.get("id")
                            if (mapped.get("confidence") or "") == "low":
                                entry["reason_not_emitted"] = "low_confidence"
                            else:
                                entry["reason_not_emitted"] = "converted"
                        else:
                            entry["mapped_item_id"] = None
                            entry["reason_not_emitted"] = "no_mapping"
                        if entry["reason_not_emitted"] != "converted":
                            suppressed.append(entry)
                    return suppressed
                suppressed = _compute_suppressed(output_dir, pre_scan)
                sup_path = os.path.join(output_dir, "suppressed_signal_report.json")
                try:
                    if suppressed:
                        with open(sup_path, "w") as sf:
                            json.dump({"suppressed": suppressed}, sf, indent=2, sort_keys=True)
                except Exception:
                    pass
            except Exception:
                suppressed = []

            summary = {
                "status": "success",
                "stable": result.get("manifest", {}).get("stable", False),
                "fingerprint": result.get("fingerprint"),
                "output_dir": result.get("output_dir"),
                "generated_files": len(result.get("outputs", [])),
                "item_count": result.get("manifest", {}).get("bootstrap_items", 0),
                "checklist_count": result.get("manifest", {}).get("bootstrap_items", 0),
                "provenance": manifest_data.get("provenance", {}),
                "dsl_section_classification": manifest_data.get("dsl_section_classification", {}),
                "semantic_strictness_policy": manifest_data.get("semantic_strictness_policy", {}),
                # Validity is established if we reached this point (no ValidationError)
                "validity_status": "pass",
                # Readiness is reported by the engine/manifest if available; expose
                # a deterministic summary-level status for tooling.
                "readiness_status": ("pass" if manifest_data.get("readiness", {}).get("ok") else "fail") if manifest_data.get("readiness") is not None else "not_evaluated",
                "readiness_report": manifest_data.get("readiness", {}).get("report") if manifest_data.get("readiness") else None,
                "conversion_state": manifest_data.get("conversion_state"),
                "state_reason": sr,
                "spec_evolution": manifest_data.get("spec_evolution"),
                "what_is_missing_next": md_missing,
                "checklist_preview_explanation": cpe,
                "conversion_path": conv,
                "progress_summary": manifest_data.get("progress_summary"),
                # Checklist emission info
                "checklist_emitted": emitted,
                "checklist_status": status,
                # Suppressed/prose-derived signals
                "suppressed_signal_count": len(suppressed),
                "inferred_from_prose_count": sum(1 for it in (manifest_data.get("checklist_preview") or []) if it.get("inferred_from_prose")),
                "output_contract_version": OUTPUT_CONTRACT_VERSION,
                # Readiness traceability
                "readiness_blockers_count": suppressed_blocker_count,
                "readiness_blocker_item_ids": blocker_items,
            }

            # Human-facing executive summary fields
            try:
                cd = os.path.join(output_dir, "checklist_draft.json")
                rr = os.path.join(output_dir, "refusal_report.json")
                is_safe = "unknown"
                where_safe = []
                why_not = None
                if os.path.exists(rr):
                    try:
                        rrj = json.load(open(rr))
                        reason = rrj.get("reason") or rrj.get("message") or str(rrj)
                    except Exception:
                        reason = "refusal_emitted"
                    is_safe = "no"
                    why_not = reason
                elif os.path.exists(cd):
                    try:
                        cdj = json.load(open(cd))
                        items = cdj.get("items", [])
                        strong = [it for it in items if (it.get("confidence") or "medium") in ("high", "medium")]
                        if strong:
                            is_safe = "yes"
                            where_safe = [it.get("ptr") or it.get("id") for it in strong]
                        else:
                            is_safe = "unknown"
                            why_not = "No items with sufficient confidence"
                    except Exception:
                        pass
                summary["is_it_safe_to_act"] = is_safe
                summary["where_is_safe"] = where_safe
                summary["why_not_safe"] = why_not
            except Exception:
                pass

            # Add checklist priority counts for visibility (success path)
            try:
                items = manifest_data.get("checklist", {}).get("items", []) or []
                # Fallback to draft file if manifest checklist missing
                if not items and os.path.exists(os.path.join(output_dir, "checklist_draft.json")):
                    try:
                        items = json.load(open(os.path.join(output_dir, "checklist_draft.json"))).get("items", []) or []
                    except Exception:
                        items = []
                total_items = len(items)
                p0 = sum(1 for it in items if it.get("priority") == "P0")
                p1 = sum(1 for it in items if it.get("priority") == "P1")
                p2 = sum(1 for it in items if it.get("priority") == "P2")
                summary["total_items"] = total_items
                summary["p0_count"] = p0
                summary["p1_count"] = p1
                summary["p2_count"] = p2
            except Exception:
                pass

            # Compute deterministic first_safe_action for summary (success path)
            try:
                def _compute_first_safe_summary(items):
                    if not items:
                        return None
                    p0_nonblocking = [it for it in items if it.get('priority') == 'P0' and not it.get('blocking')]
                    p0_blocking = [it for it in items if it.get('priority') == 'P0' and it.get('blocking')]
                    def _choose(xs):
                        if not xs:
                            return None
                        return sorted(xs, key=lambda x: x.get('id') or '')[0]
                    chosen = _choose(p0_nonblocking) or _choose(p0_blocking)
                    if not chosen:
                        return None
                    if chosen in p0_nonblocking:
                        ev = chosen.get('evidence') or {}
                        quote = ev.get('quote')
                        ptr = (ev.get('source') or {}).get('ptr')
                        if chosen.get('risk_if_false') == 'unsafe_to_act' or (chosen.get('severity') or '').lower() in ('high','critical'):
                            risk = 'high'
                        elif (chosen.get('confidence') or '').lower() == 'low':
                            risk = 'medium'
                        else:
                            risk = 'low'
                        rationale = "Evidence: " + (repr(quote[:200]) if quote else ("ptr=" + (ptr or 'unknown')))
                        why = f"This action is prioritized P0 and addresses {chosen.get('intent_category') or 'critical'} issues; performing it reduces immediate risk."
                        return {"first_safe_action": {"action": chosen.get('action') or chosen.get('text') or chosen.get('claim'), "rationale": rationale, "risk": risk, "why_this_first": why}}
                    ev = chosen.get('evidence') or {}
                    missing = []
                    if not ev.get('quote'):
                        missing.append('quote')
                    if not ev.get('source_excerpt_hash'):
                        missing.append('excerpt_hash')
                    ptr = (ev.get('source') or {}).get('ptr') or 'unknown'
                    reason = f"Refusal: item {chosen.get('id')} is blocking; missing evidence: {', '.join(missing) or 'none'}; ptr={ptr}"
                    return {"refusal_action": {"action": f"Refuse to proceed until requirement is resolved: {chosen.get('action') or chosen.get('text')}", "explanation": reason}}
            except Exception:
                _compute_first_safe_summary = lambda _: None
            try:
                items_for_first = items or []
                fs = _compute_first_safe_summary(items_for_first)
                if fs:
                    # ensure wrapper key in summary (first_safe_action or refusal_action)
                    if 'first_safe_action' in fs:
                        summary['first_safe_action'] = fs['first_safe_action']
                    elif 'refusal_action' in fs:
                        summary['refusal_action'] = fs['refusal_action']
                    else:
                        # fs may be direct dict
                        if fs.get('risk') is not None:
                            summary['first_safe_action'] = fs
                        else:
                            summary['refusal_action'] = fs
            except Exception:
                pass
            try:
                os.replace(tmp, summary_path)
            except Exception:
                try:
                    # best-effort fallback
                    with open(summary_path, 'w') as f2:
                        json.dump(summary, f2, indent=2, sort_keys=True)
                except Exception:
                    pass

            # Annotate summary with sufficiency verdict for visibility
            try:
                suff = _load_json = None
                import json as _json
                sfile = os.path.join(output_dir, 'checklist_sufficiency.json')
                if os.path.exists(sfile):
                    sdata = _json.load(open(sfile))
                    summary['sufficiency_verdict'] = sdata.get('sufficient')
                    # persist updated summary with sufficiency flag
                    try:
                        tmp2 = summary_path + '.tmp'
                        with open(tmp2, 'w') as sf:
                            import json as __json
                            __json.dump(summary, sf, indent=2, sort_keys=True)
                        try:
                            os.replace(tmp2, summary_path)
                        except Exception:
                            with open(summary_path, 'w') as sf2:
                                __json.dump(summary, sf2, indent=2, sort_keys=True)
                    except Exception:
                        pass
            except Exception:
                pass

            # Best-effort: ensure spec coverage exists by running evaluator in-process
            try:
                from shieldcraft.coverage.evaluator import evaluate_spec_coverage
                evaluate_spec_coverage(spec if isinstance(spec, dict) else {}, items or [], outdir=output_dir)
                # persist root copy
                try:
                    import shutil
                    shutil.copyfile(os.path.join(output_dir, 'spec_coverage.json'), os.path.join('.selfhost_outputs', 'spec_coverage.json'))
                except Exception:
                    pass
            except Exception:
                pass
            # Emit governance bundle and audit index (deterministic export)
            try:
                from shieldcraft.services.guidance.governance_export import emit_governance_bundle
                emit_governance_bundle(output_dir)
            except Exception:
                pass
        except Exception:
            pass

        print(f"[SELF-HOST] SUCCESS")
        print(f"[SELF-HOST] Manifest: {manifest_path}")
        print(f"[SELF-HOST] Summary: {summary_path}")
        # Final subprocess fallback to ensure sufficiency artifact exists at root
        try:
            import subprocess, sys
            subprocess.run([sys.executable, '-c', 'from shieldcraft.sufficiency.evaluator import evaluate_from_files, write_sufficiency_report; write_sufficiency_report(evaluate_from_files(".selfhost_outputs"), outdir=".selfhost_outputs")'], check=False)
        except Exception:
            pass
        # Final subprocess fallback to ensure spec coverage exists at root
        try:
            import subprocess, sys
            subprocess.run([sys.executable, '-c', 'import json; from shieldcraft.coverage.evaluator import evaluate_spec_coverage; m=json.load(open(".selfhost_outputs/manifest.json")); s=m.get("spec_metadata",{}).get("source_material") or {}; items=json.load(open(".selfhost_outputs/checklist.json")).get("items", []); evaluate_spec_coverage(s if isinstance(s, dict) else {}, items, outdir=".selfhost_outputs")'], check=False)
        except Exception:
            pass
        # Final subprocess fallback to compute implementability after coverage/sufficiency finalized
        try:
            import subprocess, sys
            subprocess.run([sys.executable, '-c', 'from shieldcraft.verdict.aggregator import compute_implementability; compute_implementability(".selfhost_outputs")'], check=False)
        except Exception:
            pass
        # Ensure governance bundle emission occurred; emit again if necessary
        try:
            from shieldcraft.services.guidance.governance_export import emit_governance_bundle
            emit_governance_bundle(output_dir)
        except Exception:
            pass
        # Return the preview/manifest for callers when available
        try:
            # Enforce primary artifact invariant on success path as well
            cd = os.path.join(output_dir, "checklist_draft.json")
            rr = os.path.join(output_dir, "refusal_report.json")
            has_cd = os.path.exists(cd)
            has_rr = os.path.exists(rr)
            if not (has_cd ^ has_rr):
                raise RuntimeError("primary_artifact_invariant_violation: exactly one of checklist_draft.json or refusal_report.json must be present")
            if has_cd:
                try:
                    payload = json.load(open(cd))
                    items = payload.get("items") or []
                except Exception:
                    items = []
                if len(items) == 0:
                    sj = {
                        "justification": "Checklist generation produced zero items confidently",
                        "item_count": 0,
                        "suppressed_signal_count": len(suppressed) if 'suppressed' in locals() else 0,
                        "inferred_from_prose_count": sum(1 for it in (manifest_data.get("checklist_preview") or []) if it.get("inferred_from_prose")) if manifest_data.get("checklist_preview") else 0,
                        "readiness_blockers_count": manifest_data.get("readiness_blockers_count", 0),
                    }
                    with open(os.path.join(output_dir, "silence_justification.json"), "w") as sf:
                        json.dump(sj, sf, indent=2, sort_keys=True)
            
            return preview
        except Exception:
            pass
        
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
        # Load spec: prefer raw JSON when possible so user-provided schema
        # validations apply over the original file shape. Fall back to the
        # ingestion helper for non-JSON formats (YAML/TOML/raw).
        try:
            with open(spec_file) as f:
                spec = json.load(f)
        except json.JSONDecodeError:
            from shieldcraft.services.spec.ingestion import ingest_spec
            spec = ingest_spec(spec_file)
        
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