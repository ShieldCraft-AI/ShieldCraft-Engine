"""Central seed manager: generate, record, and retrieve deterministic seeds."""
from typing import Dict, Optional
import os
import hashlib


def _ensure_store(engine) -> None:
    if not hasattr(engine, "_determinism_seeds"):
        engine._determinism_seeds = {}


def generate_seed(engine, name: str = "run", seed: Optional[str] = None) -> str:
    """Generate or record a seed for `name`. If seed is provided, use it; otherwise
    derive deterministically from spec fingerprint and environment.
    """
    _ensure_store(engine)
    if seed is None:
        # Deterministic default seed: fingerprint + env override
        base = getattr(engine, "_last_validated_spec_fp", "") or os.getenv("SHIELDCRAFT_DETERMINISM_BASE", "")
        seed = hashlib.sha256((name + ":" + base).encode("utf-8")).hexdigest()
    engine._determinism_seeds[name] = seed
    return seed


def get_seed(engine, name: str = "run") -> Optional[str]:
    _ensure_store(engine)
    return engine._determinism_seeds.get(name)


def snapshot(engine) -> Dict[str, str]:
    _ensure_store(engine)
    return dict(engine._determinism_seeds)


def load_snapshot(engine, snap: Dict[str, str]) -> None:
    engine._determinism_seeds = dict(snap)
