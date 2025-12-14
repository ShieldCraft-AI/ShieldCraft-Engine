**SE State (Reference)**

This short reference documents the canonical artifacts and files used to observe SE runs and their verification status.

Primary artifacts:

- `manifest.json` — run-level manifest with generated outputs and lineage.
- `summary.json` — run-level metrics and determinism flag.
- `canonical_preview.json` — canonicalized preview payload used for determinism checks.
- `generated_checklist.json` — checklist used to derive tests and enforce invariants.

Recommended checks for CI:

- Confirm `summary.json` exists and `determinism_match` is `true` for deterministic runs.
- Verify `manifest.json` and `summary.json` fingerprints match baseline expectations for self-build jobs.
