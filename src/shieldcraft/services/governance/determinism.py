import json
import hashlib
from datetime import datetime, timezone


class DeterminismEngine:
    def canonicalize(self, obj):
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def normalize_timestamp(self, ts):
        if not ts:
            return None
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def hash(self, canonical_str):
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
