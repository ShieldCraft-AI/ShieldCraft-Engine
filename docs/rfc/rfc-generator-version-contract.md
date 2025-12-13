# RFC: Generator Lockfile and generator_version Contract

Problem statement (linked tests):
- Failing tests: [tests/spec/test_pointer_missing.py::test_preflight_integration](tests/spec/test_pointer_missing.py), [tests/spec/test_pointer_strict_mode.py](tests/spec/test_pointer_strict_mode.py), [tests/test_preflight_contract.py](tests/test_preflight_contract.py)
- Summary: The preflight contract verifier checks a `generators/lockfile.json` and compares `lockfile_version` to `metadata.generator_version` in specs. A missing `generator_version` causes `GENERATOR_LOCKFILE_MISMATCH` and fails preflight. The DSL should either require `generator_version` or define a policy for missing versions.

Current observed behavior:
- `verify_generation_contract` currently enforces a strict match when `generators/lockfile.json` exists. Specs missing `metadata.generator_version` cause errors in preflight.

Proposed canonical rule:
- The `metadata.generator_version` field in the top-level spec MUST be present and MUST match the locked generator version found in `generators/lockfile.json` when that file exists.
- If `generators/lockfile.json` does not exist, generator version is optional for the spec.
- Optionally, a compatibility policy may be added to allow non-exact matches (e.g., allow `major` version match) with an explicit warning but not failing strictly.

Explicit invariants:
- Invariant: All production specs must include `metadata.generator_version` with the locked canonical version that the pipeline will use.
- Invariant: If the `lockfile.json` exists, the engine must fail the preflight with `GENERATOR_LOCKFILE_MISMATCH` only when the spec requests a different `generator_version` than lockfile — but treat missing `generator_version` as an explicit failure (so the spec authors are required to declare it).

Backward-compatibility notes:
- This RFC requires existing specs to include `metadata.generator_version`. To ease migration, provide a linter or CLI to inject `generator_version` or validate existing specs and provide remediation steps.

Out-of-scope items:
- Lockfile management and distribution processes (e.g., how to update `generators/lockfile.json`).

References:
- [verify_generation_contract](src/shieldcraft/services/generator/contract_verifier.py)
- [tests/test_preflight_contract.py](tests/test_preflight_contract.py)

