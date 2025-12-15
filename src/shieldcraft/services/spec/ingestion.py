"""Spec ingestion helper.

Contract:
- Provide a single function `ingest_spec(path: str) -> object`.
- Read raw bytes and decode using UTF-8 with `errors='replace'`.
- Try to parse structured formats in order: JSON, YAML, TOML.
- If parsing succeeds and returns dict or list, return that object.
- If all parsers fail, return the raw decoded text (string).
- Never raise due to parse/format failure.
- This module is intentionally minimal and makes no validation or canonicalization.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

def ingest_spec(path: str) -> Any:
    """Ingest a spec file at `path`.

    Returns:
        - dict or list when a structured format was parsed
        - string when parsing failed (raw content)

    This function does not perform validation or canonicalization.
    """
    p = pathlib.Path(path)
    try:
        raw_bytes = p.read_bytes()
    except Exception:
        try:
            # Fall back to text read if bytes fail
            return p.read_text(errors="replace")
        except Exception:
            return ""

    text = raw_bytes.decode("utf-8", errors="replace")

    # Try JSON
    try:
        obj = json.loads(text)
        return obj
    except Exception:
        pass

    # Try YAML (if available)
    try:
        import yaml

        try:
            obj = yaml.safe_load(text)
            return obj
        except Exception:
            pass
    except Exception:
        # PyYAML not available; skip
        pass

    # Try TOML (stdlib tomllib on py3.11+) if available
    try:
        try:
            import tomllib as _tomllib
        except Exception:
            _tomllib = None
        if _tomllib is not None:
            try:
                obj = _tomllib.loads(text)
                return obj
            except Exception:
                pass
    except Exception:
        pass

    # No structured parse succeeded; return raw text
    return text
