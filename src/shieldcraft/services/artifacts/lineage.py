import hashlib
import json


def build_lineage(product_id, spec_hash, items_hash):
    """
    Produce deterministic lineage object:
    {
      "product_id": ...,
      "spec_hash": <sha256>,
      "items_hash": <sha256>,
      "lineage_hash": <sha256 of whole object>
    }
    """
    base = {
        "product_id": product_id,
        "spec_hash": spec_hash,
        "items_hash": items_hash
    }
    h = hashlib.sha256(json.dumps(base, sort_keys=True).encode("utf-8")).hexdigest()
    base["lineage_hash"] = h
    return base


def bundle(spec_fp, items_fp, plan_fp, code_fp):
    """
    Create artifact bundle from fingerprints.
    No IO; returns structured data only.

    Returns:
        {
            "manifest": <canonical_json>,
            "signature": <sha256>,
            "paths": {...}
        }
    """
    manifest = {
        "spec_fingerprint": hashlib.sha256(spec_fp.encode()).hexdigest(),
        "items_fingerprint": hashlib.sha256(items_fp.encode()).hexdigest(),
        "plan_fingerprint": hashlib.sha256(plan_fp.encode()).hexdigest(),
        "code_fingerprint": hashlib.sha256(code_fp.encode()).hexdigest()
    }

    # Canonical JSON
    manifest_json = json.dumps(manifest, sort_keys=True)

    # Signature
    signature = hashlib.sha256(manifest_json.encode()).hexdigest()

    return {
        "manifest": manifest,
        "signature": signature,
        "paths": {
            "manifest": "manifest.json",
            "signature": "manifest.sig"
        }
    }
