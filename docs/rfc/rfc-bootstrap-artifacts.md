# RFC: Self-host Bootstrap Artifact Emissions

Problem statement (linked tests):
- Failing tests: [tests/selfhost/test_bootstrap_codegen.py](tests/selfhost/test_bootstrap_codegen.py), [tests/selfhost/test_selfhost_minimal.py](tests/selfhost/test_selfhost_minimal.py)
- Summary: Tests expect bootstrap codegen artifacts (bootstrap modules, manifests, and summary files) to be emitted during self-host runs when the spec contains bootstrap items. Current behavior: no bootstrap outputs emitted in some self-host scenarios and `summary.json` missing.

Current observed behavior:
- Self-host pipeline sometimes skips emitting `bootstrap` directory or `summary.json` when spec contains `sections.bootstrap` with `tasks` of types like `loader_stage` or `engine_stage`.
- The engine classifies items as `bootstrap` only if classification code or pointer semantics denote them as bootstrap; this behavior is not defined in the spec.

Proposed canonical rule:
- Define a canonical invariant: bootstrap section content (top-level `sections` list entries where `id` == `bootstrap` or `category` == `bootstrap`) must be deterministically mapped to `bootstrap` outputs in the self-host pipeline, emitting bootstrap modules, a `bootstrap_manifest.json`, and a `summary.json` for the run.
- The self-host pipeline must write `summary.json` for every run (empty structure if no outputs) to satisfy instrumentation and CI expectations.

Explicit invariants:
- Invariant: If the spec includes `sections` with `id: "bootstrap"` and tasks under `tasks` having `category: "bootstrap"` or type matching a canonical bootstrap typeset, the self-host pipeline MUST emit: a `bootstrap/` directory with generated files, a `bootstrap_manifest.json` in `.selfhost_outputs`, and `.selfhost_outputs/summary.json`.
- Invariant: Emitted bootstrap artifacts must carry provenance headers and deterministic lineage IDs in generation.

Backward-compatibility notes:
- Engines that previously emitted no `bootstrap` outputs will need migration: either mark relevant tasks as `category: "bootstrap"`, add a `name` field for module naming, or use [transform migration guide].
- For older specs without `generator_version`, the pipeline behavior (emit vs fail) is defined in the generator version contract RFC.

Out-of-scope items:
- Format of bootstrap module templates and Jinja2 content. The RFC only decides whether to emit artifacts and when.
- Bootstrapping policy for third-party module packaging or deployment strategies.

References:
- [test_bootstrap_codegen.py](tests/selfhost/test_bootstrap_codegen.py)
- [test_selfhost_minimal.py](tests/selfhost/test_selfhost_minimal.py)

