import json
import hashlib


def compute_bundle_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


def build_evidence_bundle(product_id, items, rollups):
    """
    Produce deterministic evidence bundle:
    {
      "product_id": ...,
      "version": "1.0",
      "items": items,
      "rollups": rollups,
      "hash": <computed>
    }
    """
    bundle = {
        "product_id": product_id,
        "version": "1.0",
        "items": items,
        "rollups": rollups
    }
    bundle["hash"] = compute_bundle_hash(bundle)
    return bundle
