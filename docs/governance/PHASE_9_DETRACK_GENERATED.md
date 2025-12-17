Phase 9: Detrack `src/generated`

Summary
-------
`src/generated/` contains deterministic build artifacts produced by the CodeGenerator pipeline. These files are reproducible from the spec and deterministic environment seeds; they are not imported at runtime. To reduce repository bloat and avoid accidental drift, `src/generated/` will be treated as a build output and excluded from version control.

Action
------
- Add `src/generated/**` to `.gitignore` (policy: build artifacts excluded).  
- CI will perform generation step before test stages to recreate artifacts deterministically.  
- Tests that assert determinism will rely on `codegen_bundle_hash` and run generation during test time (no dependence on checked-in files).

Rationale (evidence)
--------------------
- Filenames: `src/shieldcraft/services/codegen/file_plan.py` derives filenames as `sha256(item['id'])[:16]` → deterministic.  
- Content: `src/shieldcraft/services/codegen/generator.py` + `TemplateEngine` canonicalize templates and use `digest_text` for canonical SHA256 content hashing.  
- Authority: `codegen_bundle_hash` computed from sorted `(path, content-hash)` pairs; tests assert `codegen_bundle_hash` equality across runs.

Next steps
----------
1. Add CI generation step to produce `src/generated` outputs prior to tests.  
2. Add a regression test that runs generation twice and asserts `codegen_bundle_hash` equality.  
3. After CI and test guards are in place, delete `src/generated` from the repository in a normal commit (no history rewrite).
  
Enforcement
-----------
- A CI guard will run on pushes and PRs and fail the job if any files under `src/generated/` are committed.  
- Local developers should not commit generated outputs; instead run the local generation step when needed for debugging or demos: `python -m src.shieldcraft.engine --self-host --spec spec/se_dsl_v1.spec.json --dry-run --emit-preview .selfhost_outputs/selfhost_preview.json`.
