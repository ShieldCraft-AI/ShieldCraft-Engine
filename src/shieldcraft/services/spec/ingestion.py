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
from shieldcraft.services.spec.normalization import build_minimal_dsl_skeleton, adapt_sections


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

    source_format = "unknown"

    # Try JSON
    try:
        obj = json.loads(text)
        source_format = "json"
        if isinstance(obj, dict):
            # Adapt sections to array format
            if "sections" in obj:
                obj["sections"] = adapt_sections(obj["sections"])
            # If this is already a DSL-shaped dict (contains DSL top-level keys),
            # return it unchanged; otherwise promote into a minimal DSL skeleton
            if "model" in obj and "sections" in obj:
                return obj
            return build_minimal_dsl_skeleton(obj, "json")
        # wrap lists or other JSON values below
        parsed = obj
    except Exception:
        parsed = None

    # Try YAML (if available)
    if parsed is None:
        try:
            import yaml

            try:
                obj = yaml.safe_load(text)
                source_format = "yaml"
                if isinstance(obj, dict):
                    # Adapt sections to array format
                    if "sections" in obj:
                        obj["sections"] = adapt_sections(obj["sections"])
                    if "model" in obj and "sections" in obj:
                        return obj
                    return build_minimal_dsl_skeleton(obj, "yaml")
                parsed = obj
            except Exception:
                parsed = None
        except Exception:
            parsed = None

    # Try TOML (stdlib tomllib on py3.11+) if available
    if parsed is None:
        try:
            try:
                import tomllib as _tomllib
            except Exception:
                _tomllib = None
            if _tomllib is not None:
                try:
                    obj = _tomllib.loads(text)
                    source_format = "toml"
                    if isinstance(obj, dict):
                        # Adapt sections to array format
                        if "sections" in obj:
                            obj["sections"] = adapt_sections(obj["sections"])
                        if "model" in obj and "sections" in obj:
                            return obj
                        return build_minimal_dsl_skeleton(obj, "toml")
                    parsed = obj
                except Exception:
                    parsed = None
        except Exception:
            parsed = None

    # Build deterministic DSL-shaped skeleton when no dict was produced
    raw_input = parsed if parsed is not None else text
    return build_minimal_dsl_skeleton(raw_input, source_format if source_format != "unknown" else "text")
