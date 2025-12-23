"""Synthesize missing spec fields deterministically.

Provides minimal safe defaults for Tier A/B sections so the compiler can continue,
while recording what was synthesized.
"""
from typing import Dict, Tuple, List, Any
import copy

# Minimal deterministic defaults
_DEFAULTS = {
    "metadata": {"id_namespace": "default", "generator_version": "0.0"},
    "agents": [],
    "generation_mappings": {"components": [], "tasks": []},
    "artifact_contract": {"artifacts": []},
    "determinism": {"canonical_json": True, "snapshot_runs": 1},
}


def synthesize_missing_spec_fields(spec: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Return (spec_with_defaults, synthesized_keys).

    Deterministically adds safe defaults for known keys when absent or None.
    Does NOT touch unknown keys.
    """
    if spec is None:
        spec = {}
    new_spec = copy.deepcopy(spec)
    synthesized = []
    for k, v in _DEFAULTS.items():
        if k not in new_spec or new_spec.get(k) is None:
            new_spec[k] = copy.deepcopy(v)
            synthesized.append(k)
            # Attach explainability metadata to synthesized defaults by adding a section-level marker
            # Since defaults are applied to the spec object (not individual checklist items), we attach
            # a special key `_synthesized_metadata` documenting which keys were synthesized and why.
            new_spec.setdefault('_synthesized_metadata', {})
            new_spec['_synthesized_metadata'][k] = {
                'source': 'default',
                'justification': f'safe_default_{k}',
                'inference_type': 'safe_default',
                'tier': 'A' if k in (
                    "metadata",
                    "agents",
                    "evidence_bundle") else (
                    'B' if k in (
                        "determinism",
                        "artifact_contract",
                        "generation_mappings",
                        "security") else 'C')}
    # Return deterministic list of synthesized keys
    return new_spec, sorted(synthesized)
