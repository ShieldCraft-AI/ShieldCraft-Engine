import os
import json
import hashlib
from pathlib import Path
from shieldcraft.util.json_canonicalizer import canonicalize
from shieldcraft.services.spec.schema_validator import validate_spec_against_schema

SRC = Path("spec/test_spec.yml")
OUT_DIR = Path("artifacts/canonicalization")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load source YAML via safe loader
import yaml
src = yaml.safe_load(open(SRC))

# Helper
UNKNOWN = "UNKNOWN"

# Step 1: analyze and derive fields
# Derivable: metadata.product_id, metadata.product_name from system.name
system = src.get("system", {})
product_id = system.get("name") if isinstance(system.get("name"), str) else None
product_name = product_id
language = "yaml" if SRC.suffix in (".yml", ".yaml") else UNKNOWN

# Derive canonical_spec_hash from canonicalized source
canon_src = canonicalize(src)
spec_hash = hashlib.sha256(canon_src.encode()).hexdigest()

# Determinism: try to extract repeated_runs from verification.determinism.repeated_runs
determinism_section = src.get("operating_constraints", {}).get("determinism", {})
repeated_runs = determinism_section.get("verification", {}).get("repeated_runs") if determinism_section else None

# Build canonical skeleton per schema required fields
canonical = {}
# Required top-level keys from schema
required_keys = [
    "dsl_version",
    "metadata",
    "build_contract",
    "error_contract",
    "evidence_bundle",
    "domain_model",
    "capabilities",
    "state_machine",
    "determinism",
    "schema_contract",
    "artifact_contract",
    "ci_contract",
    "generation_mappings",
    "observability",
    "security",
]

# Populate metadata
metadata = {
    "product_id": product_id if product_id else UNKNOWN,
    "product_name": product_name if product_name else UNKNOWN,
    "spec_version": UNKNOWN,
    "created_at_utc": UNKNOWN,
    "owner": UNKNOWN,
    "canonical_spec_hash": spec_hash,
    "generator_version": UNKNOWN,
    "language": language,
}

# Build_contract: impossible to derive
build_contract = {
    "entrypoints": [{"id": UNKNOWN, "path": UNKNOWN}],
    "output_formats": [UNKNOWN],
}

error_contract = {"schema": UNKNOWN, "canonical_error_fields": [UNKNOWN]}

evidence_bundle = {"schema": UNKNOWN, "signing_required": UNKNOWN, "signature_algorithm": UNKNOWN}

domain_model = {"entities": []}

capabilities = {}

state_machine = {"states": [UNKNOWN], "transitions": [{"id": UNKNOWN, "from": UNKNOWN, "to": UNKNOWN}]}

# determinism
determinism = {
    "canonical_json": True if determinism_section.get("required") else UNKNOWN,
    "float_precision": UNKNOWN,
    "timestamp_format": UNKNOWN,
    "snapshot_runs": repeated_runs if repeated_runs is not None else UNKNOWN,
}

schema_contract = {"input_schemas": [UNKNOWN], "output_schemas": [UNKNOWN], "validation_required": UNKNOWN}

artifact_contract = {"artifacts": [UNKNOWN], "canonical_hash_algorithm": UNKNOWN}

ci_contract = {"required_jobs": [UNKNOWN]}

generation_mappings = {"trace": UNKNOWN}

observability = {"execution_state": [UNKNOWN]}

security = {"policies": [UNKNOWN]}

# dsl_version left as UNKNOWN per no-guessing
canonical["dsl_version"] = UNKNOWN
canonical["metadata"] = metadata
canonical["build_contract"] = build_contract
canonical["error_contract"] = error_contract
canonical["evidence_bundle"] = evidence_bundle
canonical["domain_model"] = domain_model
canonical["capabilities"] = capabilities
canonical["state_machine"] = state_machine
canonical["determinism"] = determinism
canonical["schema_contract"] = schema_contract
canonical["artifact_contract"] = artifact_contract
canonical["ci_contract"] = ci_contract
canonical["generation_mappings"] = generation_mappings
canonical["observability"] = observability
canonical["security"] = security

# Write canonical spec
out_spec = OUT_DIR / "generated_canonical_spec.json"
out_spec.write_text(json.dumps(canonical, indent=2, sort_keys=True))

# Step 3: produce gap report
missing_required_fields = [k for k, v in canonical.items() if v == UNKNOWN or (isinstance(v, dict) and any(vv == UNKNOWN or (isinstance(vv, list) and UNKNOWN in vv) for vv in v.values()))]
ambiguous_sections = ["build_contract", "error_contract", "evidence_bundle", "state_machine", "schema_contract", "artifact_contract", "ci_contract", "generation_mappings", "observability", "security"]
blocked_generation_reasons = []
if metadata["product_id"] == UNKNOWN:
    blocked_generation_reasons.append("missing_product_id")
if build_contract["entrypoints"][0]["id"] == UNKNOWN:
    blocked_generation_reasons.append("missing_entrypoints")

gap_report = {
    "missing_required_fields": missing_required_fields,
    "ambiguous_sections": ambiguous_sections,
    "blocked_generation_reasons": blocked_generation_reasons,
}

out_gaps = OUT_DIR / "spec_gaps.json"
out_gaps.write_text(json.dumps(gap_report, indent=2, sort_keys=True))

# Step 4: validate against schema
schema_path = "spec/schemas/se_dsl_v1.schema.json"
valid, errors = validate_spec_against_schema(canonical, schema_path)

validation_report = {"valid": valid, "errors": errors}
(out_gaps.parent / "schema_validation.json").write_text(json.dumps(validation_report, indent=2, sort_keys=True))

# Check that all errors correspond to fields set to UNKNOWN
errors_about_unknown = []
for e in errors:
    # rudimentary check: if 'UNKNOWN' appears in instance value in error message
    if "UNKNOWN" in json.dumps(canonical):
        errors_about_unknown.append(e)

print(json.dumps({"written_spec": str(out_spec), "gaps": str(out_gaps), "validation": validation_report}, indent=2))
