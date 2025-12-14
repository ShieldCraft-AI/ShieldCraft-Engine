# SE Repository Inventory (Authoritative, factual)

Generated: 2025-12-14
Source: workspace root (deterministic listing, depth=4)

---

**1) Deterministic tree listing (depth 4, sorted)**

(Only file paths shown; truncated beyond depth 4 as requested)

```
./artifacts
./artifacts/cleanup
./artifacts/cleanup/placeholder_inventory.json
./artifacts/determinism
./artifacts/determinism/check.txt
./artifacts/determinism/run1
./artifacts/determinism/run1/generators_lockfile.json
... (truncated in this listing but present in repo)
./ci
./ci/selfhost_dryrun.yml
./copilot-instructions.md
./docs
./docs/decision_log.md
... (docs tree present)
./generators/lockfile.json
./list_tree.sh
./pyproject.toml
./scripts
./scripts/dsl_runtime_reflector.py
./scripts/run_generator_verify.py
./spec
./spec/schemas/se_dsl_v1.schema.json
./spec/se_dsl_v1.spec.json
./src
./src/generated
./src/shieldcraft
./src/shieldcraft/dsl/loader.py
./src/shieldcraft/engine.py
./src/shieldcraft/main.py
./src/shieldcraft/services/checklist
./src/shieldcraft/services/spec
./src/shieldcraft/services/governance
./src/shieldcraft/services/codegen
./src/shieldcraft/services/preflight
./src/shieldcraft/services/validator
./src/shieldcraft/services/selfhost
./tests
./tests/checklist
./tests/engine
./tests/spec
```

---

**2) Component presence by target (facts observed in code/docs only)**n
- engine/core:
  - Present: `src/shieldcraft/engine.py` (defines class `Engine` with methods: `run`, `generate_code`, `run_self_host`, `execute`, `generate_evidence`). Also `src/shieldcraft/engine_batch.py` exists.
  - Files: `src/shieldcraft/engine.py`, `src/shieldcraft/engine_batch.py`.

- runtime:
  - Observed artifacts: `scripts/dsl_runtime_reflector.py` (runtime field extraction script), and a `runtime` classification reference in `src/shieldcraft/services/checklist/classify.py`.
  - No dedicated `runtime` package/module (e.g., `src/shieldcraft/runtime.py`) discovered at depth ≤4.
  - Files: `scripts/dsl_runtime_reflector.py`, `src/shieldcraft/services/checklist/classify.py`.

- instruction issuance:
  - Evidence of instruction templates and invariants (docs): `docs/se_instruction_template_v1.json`, `docs/se_instruction_invariants_v1.md`.
  - Checklist generation code that produces tasks is present: `src/shieldcraft/services/checklist/generator.py` and related modules under `src/shieldcraft/services/checklist/`.
  - Files: `docs/se_instruction_template_v1.json`, `docs/se_instruction_invariants_v1.md`, `src/shieldcraft/services/checklist/generator.py`.

- instruction validation:
  - A `validator` package exists at `src/shieldcraft/services/validator` (observed `__init__.py`).
  - No implementation modules (functions/classes) explicitly named for instruction validation were found in `src/shieldcraft/services/validator` at depth ≤4.
  - Files: `src/shieldcraft/services/validator/__init__.py` (no other validator modules observed at depth ≤4). **Status: UNKNOWN (no validation code observable beyond package presence).**

- persona loading/runtime:
  - Persona descriptions exist in docs: `docs/Fiona.txt` and `docs/product.yml` includes persona entries.
  - No code module named `persona`, `persona_loader`, or similar was found at depth ≤4.
  - Files: `docs/Fiona.txt`, `docs/product.yml`. **Status: UNKNOWN (no persona runtime code observable).**

- spec handling:
  - Present: DSL loader, canonical loader, schema files, spec utils.
  - Files: `src/shieldcraft/dsl/loader.py`, `src/shieldcraft/dsl/canonical_loader.py`, `spec/schemas/se_dsl_v1.schema.json`, `spec/se_dsl_v1.spec.json`, `src/shieldcraft/services/spec/*` (schema validator, pointer auditor, model, fingerprint utilities).

- checklist handling:
  - Present: `src/shieldcraft/services/checklist` with modules: `generator.py`, `model.py`, `derived.py`, `invariants.py`, `order.py`, `extractor.py`, `normalization_audit.py`, `classify.py` and tests in `tests/checklist/`.
  - Files: `src/shieldcraft/services/checklist/*` (multiple files enumerated in repository tree).

---

**3) Entry points (file paths only, factual)**
- `src/shieldcraft/main.py` (module with `main()` and CLI flags: `--self-host`, `--validate-spec`, `--generate`, etc.).
- `src/shieldcraft/engine.py` (class `Engine` used by CLI and tests).
- `src/shieldcraft/engine_batch.py` (batch runner file present).
- `scripts/run_generator_verify.py` (script present in `scripts/`).
- Note: `pyproject.toml` does not declare `console_scripts` entry points (no scripts mapped there). Tests invoke the CLI via `python -m shieldcraft.main` (observable usage in tests).

---

**4) Test inventory (directories and filenames only)**
- `tests/ast/`:
  - `test_ast_builder.py`
  - `test_ast_queries.py`
  - `test_completeness.py`
  - `test_consistency.py`
  - `test_lineage_consistency.py`

- `tests/checklist/`:
  - `test_ancestry.py`
  - `test_ast_integration.py`
  - `test_classification_types.py`
  - `test_cross_section_order.py`
  - `test_cycles.py`
  - `test_derived.py`
  - `test_derived_determinism.py`
  - `test_id_collision.py`
  - `test_implicit_deps.py`
  - `test_integration_items.py`
  - `test_invariants.py`
  - `test_ordering_stability.py`
  - `test_resolution_chain.py`
  - `test_timings.py`

- `tests/codegen/`:
  - `test_codegen_roundtrip.py`
  - `test_dry_run.py`
  - `test_provenance_headers.py`
  - `test_template_engine.py`
  - `test_templates_render.py`
  - `test_template_validation.py`

- `tests/engine/`:
  - `test_batch.py`
  - `test_engine_end_to_end.py`

- `tests/selfhost/`:
  - `test_basic_selfhost_pipeline.py`
  - `test_bootstrap_codegen.py`
  - `test_governance_and_pointers.py`
  - `test_selfhost_dryrun.py`
  - `test_selfhost_minimal.py`

- `tests/spec/` (selection):
  - `test_canonical_loader_roundtrip.py`
  - `test_dsl_authority_lock.py`
  - `test_format_check.py`
  - `test_pointer_map.py`
  - `test_pointer_missing.py`
  - `test_pointer_strict_mode.py`

- Root-level test files (examples):
  - `tests/test_checklist.py`
  - `tests/test_engine.py`
  - `tests/test_governance_evidence.py`
  - ... (numerous test files present at repository root and subdirectories; see `tests/` tree above)

---

**5) Explicit unknowns (components not confirmed by inspecting code at depth ≤4)**
- `instruction validation` implementation: `src/shieldcraft/services/validator` exists but contains only `__init__.py` at depth ≤4. No concrete instruction validation modules were observed — mark as **UNKNOWN**.
- `persona loading/runtime`: Personas are documented (`docs/Fiona.txt`) but no runtime loading code (e.g., `persona_loader`) was found — mark as **UNKNOWN**.
- `dedicated runtime module`: No module named `runtime` or `runtime_manager` located at depth ≤4; some runtime-related scripts exist (`scripts/dsl_runtime_reflector.py`) — treat as **PARTIAL (no dedicated runtime module observed)**.

---

Notes & constraints:
- This inventory is strictly factual and based on repository contents up to depth 4 and exact file names/paths. No code modifications were made.
- Where evidence is inconclusive the token `UNKNOWN` is used as required.

---

If you want, I can:
- Expand the deterministic tree listing to greater depth or produce a full file-by-file CSV.
- Create issue skeletons for `UNKNOWN` components to request clarifying implementation or owners.

