import pathlib
import hashlib
from datetime import datetime, timezone


class ProvenanceEngine:
    def compute_file_hash(self, path):
        p = pathlib.Path(path)
        if not p.exists():
            return None
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def timestamp(self):
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def build_record(self, *, spec_path, engine_version, checklist_hash):
        return {
            "spec_sha256": self.compute_file_hash(spec_path),
            "engine_version": engine_version,
            "checklist_hash": checklist_hash,
            "timestamp_utc": self.timestamp()
        }
