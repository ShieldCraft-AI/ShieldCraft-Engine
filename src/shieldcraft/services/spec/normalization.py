"""DSL normalization helpers.

Provide lightweight utilities to lift arbitrary input into a minimal,
deterministic SE DSL v1 skeleton so downstream validators and diagnostics
operate in DSL terms. This module avoids inventing semantics and uses
deterministic placeholders only.
"""
from __future__ import annotations

from typing import Any, Dict


CANONICAL_SPEC_FORMAT = "canonical_json_v1"


def build_minimal_dsl_skeleton(raw_input: Any, source_format: str | None = None) -> Dict[str, Any]:
    """Return a minimal DSL-shaped dict that preserves `raw_input`.

    Rules:
    - Must include top-level `metadata`, `model`, and `sections` keys.
    - `metadata` contains deterministic placeholders: `product_id`, `spec_version`,
      `spec_format`, and `normalized` flag.
    - Preserve `raw_input` under `metadata.source_material` for diagnostics.
    - Do not add instruction semantics (no `invariants`/`instructions` unless present).
    - Adapt sections: if dict, convert to array format.
    """
    md = {
        "product_id": "unknown",
        "spec_version": "0.0",
        "spec_format": CANONICAL_SPEC_FORMAT,
        "normalized": True,
    }
    if source_format:
        md["source_format"] = source_format
    # Attach raw input deterministically for diagnostics and provenance.
    md["source_material"] = raw_input

    sections = {}
    if isinstance(raw_input, dict) and "sections" in raw_input:
        sections = adapt_sections(raw_input["sections"])
    elif isinstance(raw_input, dict):
        # If raw_input is dict but no sections, check if it has other keys that could be sections
        # For now, keep empty
        pass

    skeleton = {
        "metadata": md,
        "model": {},
        "sections": sections,
    }
    return skeleton


def adapt_sections(sections: Any) -> list:
    """Adapt sections to array format if it's a dict."""
    if isinstance(sections, list):
        return sections
    elif isinstance(sections, dict):
        # Convert dict like {"main": ["task1"]} to [{"id": "main", "tasks": ["task1"]}]
        adapted = []
        for name, tasks in sections.items():
            if isinstance(tasks, list):
                adapted.append({"id": name, "tasks": tasks})
            else:
                # If tasks is not a list, wrap it
                adapted.append({"id": name, "tasks": [str(tasks)]})
        return adapted
    else:
        # If not dict or list, return empty array
        return []
