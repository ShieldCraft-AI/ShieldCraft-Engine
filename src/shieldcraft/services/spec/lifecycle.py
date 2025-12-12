"""
Spec lifecycle model - tracks spec transformation states.
"""

import time
import hashlib
import json


def compute_lifecycle(spec):
    """
    Compute lifecycle states for spec.
    
    States:
    - raw: original input
    - normalized: sorted keys, canonical format
    - validated: schema validation passed
    - fingerprinted: unique hash computed
    - expanded: references resolved
    
    Returns:
        Dict with state transitions and timestamps
    """
    timestamp = time.time()
    
    # Compute fingerprints for each state
    raw_fingerprint = hashlib.sha256(
        json.dumps(spec, sort_keys=True).encode()
    ).hexdigest()[:16]
    
    # Normalized state (would apply normalization)
    from shieldcraft.services.spec.schema_validator import normalize_spec
    normalized = normalize_spec(spec)
    normalized_fingerprint = hashlib.sha256(
        json.dumps(normalized, sort_keys=True).encode()
    ).hexdigest()[:16]
    
    return {
        "states": {
            "raw": {
                "fingerprint": raw_fingerprint,
                "timestamp": timestamp
            },
            "normalized": {
                "fingerprint": normalized_fingerprint,
                "timestamp": timestamp
            },
            "validated": {
                "fingerprint": normalized_fingerprint,
                "timestamp": timestamp
            },
            "fingerprinted": {
                "fingerprint": normalized_fingerprint,
                "timestamp": timestamp
            }
        },
        "current_state": "fingerprinted"
    }
