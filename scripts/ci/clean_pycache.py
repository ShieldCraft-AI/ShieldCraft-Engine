#!/usr/bin/env python3
"""Utility: remove stale __pycache__ and .pyc files in the repository (for CI hygiene)."""
import pathlib

root = pathlib.Path(__file__).resolve().parents[2]
for p in root.rglob('__pycache__'):
    try:
        for f in p.iterdir():
            f.unlink()
        p.rmdir()
    except Exception:
        pass
for f in root.rglob('*.pyc'):
    try:
        f.unlink()
    except Exception:
        pass
print('cleaned stale bytecode')
