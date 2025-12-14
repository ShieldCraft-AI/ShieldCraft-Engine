SE Self-Build
===============

This document describes the SE self-build process and guarantees.

Key points:
- Invocation: use `Engine.run_self_build(spec_path, dry_run=False)` or the CI job `.github/workflows/selfbuild.yml`.
- Preconditions: repository must be in sync (`repo_state_sync.json`), clean worktree, and `snapshot` authority is default.
- Outputs: emitted under `artifacts/self_build/<fingerprint>/` and include `repo_snapshot.json`, `bootstrap_manifest.json`, and `self_build_manifest.json`.
- Identity contract: `repo_snapshot.json` and `bootstrap_manifest.json` are treated as bitwise identity artifacts and are subject to parity checks.
- Diff guard: `Engine.verify_self_build_output(output_dir)` checks emitted `repo_snapshot.json` matches the current repo snapshot and fails on mismatch.
- Provenance: manifests include `previous_snapshot` and `build_depth` fields; emitted artifacts include deterministic provenance headers.

Failure modes:
- Missing snapshot: `selfbuild_missing_snapshot`
- Mismatch detected: `selfbuild_mismatch`
- Recursive invocation prevented: `selfbuild_recursive_invocation`

See tests in `tests/selfbuild/` for concrete expected behavior.
