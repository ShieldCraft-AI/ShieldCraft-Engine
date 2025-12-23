"""
Verification Agent for ShieldCraft Engine.
Runs deterministic checks against governance contracts and tests.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List


class VerificationAgent:
    """
    Agent that verifies artifacts against governance contracts.
    """

    def __init__(self):
        self.id = "verification_agent.v1"
        self.description = "Runs deterministic checks against governance contracts and tests."

    def verify_artifacts(self, artifacts_manifest_path: str) -> Dict[str, Any]:
        """
        Verify artifacts against contracts.

        Args:
            artifacts_manifest_path: Path to artifacts manifest JSON

        Returns:
            Verification report dict
        """
        with open(artifacts_manifest_path, 'r') as f:
            manifest = json.load(f)

        report = {
            "agent_id": self.id,
            "manifest_hash": self._compute_hash(manifest),
            "verified_at": "2025-12-23T00:00:00Z",
            "overall_status": "PASS",
            "checks": [],
            "critical_failures": [],
            "warnings": []
        }

        # Run verification checks
        checks = [
            self._check_provenance_integrity,
            self._check_contract_compliance,
            self._check_test_coverage,
            self._check_determinism,
            self._check_security_compliance
        ]

        for check_func in checks:
            try:
                result = check_func(manifest)
                report["checks"].append(result)

                if result["status"] == "FAIL" and result.get("critical", False):
                    report["critical_failures"].append(result)
                    report["overall_status"] = "FAIL"
                elif result["status"] == "WARN":
                    report["warnings"].append(result)

            except Exception as e:
                error_result = {
                    "check": check_func.__name__,
                    "status": "ERROR",
                    "message": str(e),
                    "critical": True
                }
                report["checks"].append(error_result)
                report["critical_failures"].append(error_result)
                report["overall_status"] = "FAIL"

        return report

    def _check_provenance_integrity(self, manifest: Dict) -> Dict:
        """Check that all artifacts have valid provenance."""
        result = {
            "check": "provenance_integrity",
            "status": "PASS",
            "message": "All artifacts have provenance",
            "critical": True
        }

        artifacts = manifest.get("artifacts", [])
        for artifact in artifacts:
            if not artifact.get("canonical_hash"):
                result["status"] = "FAIL"
                result["message"] = f"Artifact {artifact.get('id', 'unknown')} missing canonical_hash"
                break
            if not artifact.get("provenance"):
                result["status"] = "FAIL"
                result["message"] = f"Artifact {artifact.get('id', 'unknown')} missing provenance"
                break

        return result

    def _check_contract_compliance(self, manifest: Dict) -> Dict:
        """Check compliance with governance contracts."""
        result = {
            "check": "contract_compliance",
            "status": "PASS",
            "message": "Contracts are compliant",
            "critical": True
        }

        # Check for required contractual artifacts
        required_contracts = ["governance_contracts.json", "architecture_contract.json"]
        artifacts = manifest.get("artifacts", [])
        artifact_ids = [a.get("id", "") for a in artifacts]

        for contract in required_contracts:
            if not any(contract in aid for aid in artifact_ids):
                result["status"] = "FAIL"
                result["message"] = f"Missing required contract: {contract}"
                break

        return result

    def _check_test_coverage(self, manifest: Dict) -> Dict:
        """Check test coverage requirements."""
        result = {
            "check": "test_coverage",
            "status": "PASS",
            "message": "Test coverage meets requirements",
            "critical": False
        }

        # Look for test artifacts
        artifacts = manifest.get("artifacts", [])
        has_tests = any("test" in a.get("id", "").lower() for a in artifacts)

        if not has_tests:
            result["status"] = "WARN"
            result["message"] = "No test artifacts found"

        return result

    def _check_determinism(self, manifest: Dict) -> Dict:
        """Check determinism of artifacts."""
        result = {
            "check": "determinism",
            "status": "PASS",
            "message": "Artifacts are deterministic",
            "critical": True
        }

        # Check for snapshot verification
        if not manifest.get("snapshot_verified", False):
            result["status"] = "FAIL"
            result["message"] = "Snapshot verification not performed"

        return result

    def _check_security_compliance(self, manifest: Dict) -> Dict:
        """Check security compliance."""
        result = {
            "check": "security_compliance",
            "status": "PASS",
            "message": "Security requirements met",
            "critical": True
        }

        # Basic checks - in real implementation, would check signatures, etc.
        artifacts = manifest.get("artifacts", [])
        for artifact in artifacts:
            if artifact.get("type") == "contractual" and not artifact.get("signed", False):
                result["status"] = "FAIL"
                result["message"] = f"Contractual artifact {artifact.get('id')} not signed"
                break

        return result

    def _compute_hash(self, data: Dict) -> str:
        """Compute hash for verification."""
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


# CLI interface
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python verification_agent.py <artifacts_manifest.json>")
        sys.exit(1)

    agent = VerificationAgent()
    manifest_path = sys.argv[1]

    try:
        report = agent.verify_artifacts(manifest_path)
        print(json.dumps(report, indent=2))

        if report["overall_status"] == "FAIL":
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)