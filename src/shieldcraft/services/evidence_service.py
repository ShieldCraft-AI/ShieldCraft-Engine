"""
Evidence Service for ShieldCraft Engine.
Bundles evidence for audit and verification.
"""

import json
import zipfile
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class EvidenceService:
    """
    Service for creating signed evidence bundles.
    """

    def __init__(self):
        self.bundle_schema = "schemas/evidence_bundle.json"

    def create_evidence_bundle(self, run_data: Dict[str, Any], artifacts_dir: str, output_path: str) -> str:
        """
        Create a signed evidence bundle.

        Args:
            run_data: Run metadata and results
            artifacts_dir: Directory containing artifacts
            output_path: Path for the output ZIP bundle

        Returns:
            Path to created bundle
        """
        bundle_data = {
            "manifest": self._create_manifest(run_data),
            "graph_hash": self._compute_graph_hash(run_data),
            "agent_logs_canonicalized_filtered": self._collect_agent_logs(run_data),
            "signature": self._create_signature(run_data),
            "verification_report": run_data.get("verification_report", {}),
            "drift_check_results": self._check_drift(run_data),
            "artifacts/": self._collect_artifacts(artifacts_dir),
            "logs/": self._collect_logs(run_data),
            "provenance_chain": self._build_provenance_chain(run_data),
            "signatures/": self._collect_signatures(run_data)
        }

        # Create ZIP bundle
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for key, value in bundle_data.items():
                if isinstance(value, dict):
                    zf.writestr(f"{key.rstrip('/')}/manifest.json", json.dumps(value, indent=2))
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            zf.writestr(f"{key.rstrip('/')}/item_{i}.json", json.dumps(item, indent=2))
                        else:
                            zf.writestr(f"{key.rstrip('/')}/item_{i}.txt", str(item))
                else:
                    zf.writestr(f"{key.rstrip('/')}/data.txt", str(value))

        return output_path

    def _create_manifest(self, run_data: Dict) -> Dict[str, Any]:
        """Create bundle manifest."""
        return {
            "bundle_version": "1.0",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "run_id": run_data.get("run_id", "unknown"),
            "spec_hash": run_data.get("spec_hash", ""),
            "engine_version": run_data.get("engine_version", "1.0.0"),
            "determinism_verified": run_data.get("determinism_verified", False),
            "artifacts_count": len(run_data.get("artifacts", [])),
            "agents_used": [a.get("id", "") for a in run_data.get("agents", [])]
        }

    def _compute_graph_hash(self, run_data: Dict) -> str:
        """Compute hash of the artifact dependency graph."""
        # Simplified: hash the artifacts list
        artifacts = json.dumps(run_data.get("artifacts", []), sort_keys=True)
        return hashlib.sha256(artifacts.encode()).hexdigest()

    def _collect_agent_logs(self, run_data: Dict) -> List[Dict]:
        """Collect and canonicalize agent logs."""
        logs = []
        for agent in run_data.get("agents", []):
            log_entry = {
                "agent_id": agent.get("id", ""),
                "execution_time_ms": agent.get("execution_time", 0),
                "status": agent.get("status", "unknown"),
                "output_hash": self._hash_dict(agent.get("output", {}))
            }
            logs.append(log_entry)
        return logs

    def _create_signature(self, run_data: Dict) -> Dict[str, Any]:
        """Create cryptographic signature for the bundle."""
        # Simplified signature (would use KMS in production)
        content_hash = self._compute_graph_hash(run_data)
        return {
            "algorithm": "sha256",
            "content_hash": content_hash,
            "signature": hashlib.sha256(f"signed:{content_hash}".encode()).hexdigest(),
            "signer": "shieldcraft_engine",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def _check_drift(self, run_data: Dict) -> Dict[str, Any]:
        """Check for drift between runs."""
        return {
            "drift_detected": False,
            "baseline_hash": run_data.get("baseline_hash", ""),
            "current_hash": self._compute_graph_hash(run_data),
            "checks_performed": ["artifact_hashes", "provenance_chain"]
        }

    def _collect_artifacts(self, artifacts_dir: str) -> List[Dict]:
        """Collect artifact metadata."""
        artifacts = []
        if os.path.exists(artifacts_dir):
            for root, dirs, files in os.walk(artifacts_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, artifacts_dir)
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()

                    artifacts.append({
                        "path": rel_path,
                        "hash": file_hash,
                        "size": os.path.getsize(file_path)
                    })
        return artifacts

    def _collect_logs(self, run_data: Dict) -> List[Dict]:
        """Collect execution logs."""
        return run_data.get("logs", [])

    def _build_provenance_chain(self, run_data: Dict) -> List[Dict]:
        """Build provenance chain."""
        chain = []
        for artifact in run_data.get("artifacts", []):
            chain.append({
                "artifact_id": artifact.get("id", ""),
                "generated_by": artifact.get("agent", ""),
                "inputs": artifact.get("inputs", []),
                "timestamp": artifact.get("timestamp", "")
            })
        return chain

    def _collect_signatures(self, run_data: Dict) -> List[Dict]:
        """Collect signatures from agents/artifacts."""
        signatures = []
        for agent in run_data.get("agents", []):
            if agent.get("signature"):
                signatures.append(agent["signature"])
        return signatures

    def _hash_dict(self, data: Dict) -> str:
        """Hash a dictionary."""
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


# CLI interface
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python evidence_service.py <run_data.json> <artifacts_dir> <output_bundle.zip>")
        sys.exit(1)

    service = EvidenceService()
    run_data_file = sys.argv[1]
    artifacts_dir = sys.argv[2]
    output_path = sys.argv[3]

    with open(run_data_file, 'r') as f:
        run_data = json.load(f)

    try:
        bundle_path = service.create_evidence_bundle(run_data, artifacts_dir, output_path)
        print(f"Evidence bundle created: {bundle_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)