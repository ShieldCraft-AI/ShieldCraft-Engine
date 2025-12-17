# Test Collection Audit

Date: 2025-12-17

Summary: The following pytest collection/import errors were observed when running `pytest -q` from repo root.

Failing entries (observed):

1) ERROR collecting tests/plan/test_execution_plan.py
   - Error: import file mismatch
   - Details: imported module 'test_execution_plan' has __file__ attribute pointing to `/tests/checklist/test_execution_plan.py` while test file being collected is `/tests/plan/test_execution_plan.py`.
   - Root cause: duplicate test basenames across different directories causing pytest import module name collisions (name-collision / stale pyc influence).
   - Classification: name-collision (stale __pycache__ can exacerbate this)

2) ERROR collecting tests/requirements/test_completeness.py
   - Error: import file mismatch
   - Details: imported module 'test_completeness' points to `/tests/ast/test_completeness.py` while collected file is `/tests/requirements/test_completeness.py`.
   - Root cause: duplicate basename `test_completeness.py` in separate test packages.
   - Classification: name-collision

3) ERROR collecting tests/requirements/test_extractor.py
   - Error: import file mismatch
   - Details: imported module 'test_extractor' points to `/tests/test_extractor.py` while collected file is `/tests/requirements/test_extractor.py`.
   - Root cause: duplicate basename `test_extractor.py`.
   - Classification: name-collision

4) ERROR collecting tests/sufficiency/test_sufficiency.py
   - Error: import file mismatch
   - Details: imported module 'test_sufficiency' points to `/tests/requirements/test_sufficiency.py` while collected file is `/tests/sufficiency/test_sufficiency.py`.
   - Root cause: duplicate basename `test_sufficiency.py`.
   - Classification: name-collision

Notes:
- These are all name-collision issues (multiple tests with identical module basenames). Pytest's import mechanism maps module names (based on basenames) which can conflict when multiple tests share the same file name in different subdirectories; stale .pyc/__pycache__ exacerbates the issue.
- No production code changes are required; fixes are test-only (renames + pytest config + guard tests + cleanup helpers).

Next steps (Phase 16 plan):
- Normalize duplicate filenames deterministically (append category prefix/suffix).
- Add pytest configuration (pytest.ini) with explicit `testpaths` and `norecursedirs` entries.
- Add `tests/conftest.py` session setup to set `PYTHONDONTWRITEBYTECODE=1` and ensure `src` is on `sys.path` for absolute imports.
- Add guard tests: duplicate basename detector and 'no relative imports' detector.
- Add cleanup script to remove stale `__pycache__` and `.pyc` files.
- Add authoritative governance doc `docs/governance/TEST_COLLECTION_STABILITY_CONTRACT.md` and update `decision_log.md` (Phase 16 closed).
