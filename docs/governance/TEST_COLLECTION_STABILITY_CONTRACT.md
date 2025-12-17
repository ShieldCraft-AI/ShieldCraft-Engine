# Test Collection Stability Contract (AUTHORITATIVE)

Decision: AUTHORITATIVE — Phase 16: Test & CI Stability Locked

Summary
- Pytest collection must be deterministic and robust to local bytecode artifacts and duplicate basenames. CI must run the full test suite with zero collection/import errors.

Rules
- Duplicate test basenames across directories are disallowed. CI will fail the run if duplicates are detected.
- Tests must not rely on relative imports; absolute imports via `shieldcraft.*` are preferred.
- Bytecode cache pollution (`__pycache__`, `.pyc`) must be removed or ignored during CI runs. CI will include a cleanup step (`scripts/ci/clean_pycache.py`) to enforce this.
- Pytest configuration is authoritative and stored in `pytest.ini` with explicit `testpaths` and `norecursedirs` to prevent spurious discovery.

Enforcement
- Guard tests added: `tests/ci/test_no_duplicate_test_basenames.py`, `tests/ci/test_no_relative_imports.py`.
- CI/maintainers: ensure `scripts/ci/clean_pycache.py` is invoked in CI pre-step; don't rely on ephemeral local caches.

Rationale
- Prevents brittle, environment-dependent failures during CI by eliminating common sources of import/collection errors.

Status: AUTHORITATIVE (locked)
