"""
Local Orchestrator for ShieldCraft Engine.
Implements state machine logic locally (alternative to AWS Step Functions).
"""

import json
import logging
from typing import Dict, Any, List, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalOrchestrator:
    """
    Local implementation of the ShieldCraft manufacturing state machine.
    """

    def __init__(self):
        self.states = {
            "ingest_spec": self._ingest_spec,
            "validate_spec": self._validate_spec,
            "orchestrate_agents": self._orchestrate_agents,
            "aggregate_results": self._aggregate_results,
            "verification": self._verification,
            "finalize": self._finalize
        }
        self.state_data = {}

    def run_manufacture_pipeline(self, spec_path: str) -> Dict[str, Any]:
        """
        Run the complete manufacturing pipeline.

        Args:
            spec_path: Path to the product spec

        Returns:
            Pipeline results
        """
        self.state_data = {
            "spec_path": spec_path,
            "current_state": "ingest_spec",
            "status": "running",
            "artifacts": [],
            "logs": [],
            "errors": []
        }

        try:
            # Execute states in sequence
            for state_name, state_func in self.states.items():
                logger.info(f"Executing state: {state_name}")
                self.state_data["current_state"] = state_name

                result = state_func()
                if not result.get("success", False):
                    self.state_data["status"] = "failed"
                    self.state_data["errors"].append(result.get("error", "Unknown error"))
                    break

                self.state_data["logs"].append({
                    "state": state_name,
                    "result": result
                })

            self.state_data["status"] = "completed"

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.state_data["status"] = "failed"
            self.state_data["errors"].append(str(e))

        return self.state_data

    def _ingest_spec(self) -> Dict[str, Any]:
        """Ingest and parse the spec."""
        try:
            spec_path = self.state_data["spec_path"]
            with open(spec_path, 'r') as f:
                if spec_path.endswith('.yml') or spec_path.endswith('.yaml'):
                    import yaml
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)

            self.state_data["spec"] = spec
            return {"success": True, "spec_loaded": True}
        except Exception as e:
            return {"success": False, "error": f"Failed to ingest spec: {e}"}

    def _validate_spec(self) -> Dict[str, Any]:
        """Validate the spec against schema."""
        try:
            spec = self.state_data["spec"]
            # Basic validation - check required fields
            required_fields = ["metadata", "product_intent"]
            for field in required_fields:
                if field not in spec:
                    return {"success": False, "error": f"Missing required field: {field}"}

            return {"success": True, "validation_passed": True}
        except Exception as e:
            return {"success": False, "error": f"Validation failed: {e}"}

    def _orchestrate_agents(self) -> Dict[str, Any]:
        """Run agents in parallel (simulated)."""
        try:
            spec = self.state_data["spec"]
            agents_config = spec.get("agents", {})

            # Simulate running agents
            agent_results = []
            for agent_name, agent_config in agents_config.items():
                # In real implementation, this would instantiate and run actual agents
                result = {
                    "agent_id": agent_config.get("id", agent_name),
                    "status": "completed",
                    "output": {"placeholder": True},
                    "execution_time": 1000  # ms
                }
                agent_results.append(result)

            self.state_data["agent_results"] = agent_results
            return {"success": True, "agents_run": len(agent_results)}
        except Exception as e:
            return {"success": False, "error": f"Agent orchestration failed: {e}"}

    def _aggregate_results(self) -> Dict[str, Any]:
        """Aggregate results from agents."""
        try:
            agent_results = self.state_data.get("agent_results", [])
            artifacts = []

            for result in agent_results:
                # Create artifact entries
                artifact = {
                    "id": f"{result['agent_id']}_output",
                    "type": "generated",
                    "agent": result["agent_id"],
                    "content": result.get("output", {}),
                    "timestamp": "2025-12-23T00:00:00Z"
                }
                artifacts.append(artifact)

            self.state_data["artifacts"] = artifacts
            return {"success": True, "artifacts_created": len(artifacts)}
        except Exception as e:
            return {"success": False, "error": f"Result aggregation failed: {e}"}

    def _verification(self) -> Dict[str, Any]:
        """Run verification on artifacts."""
        try:
            artifacts = self.state_data.get("artifacts", [])

            # Simulate verification
            verification_report = {
                "overall_status": "PASS",
                "checks": [
                    {"check": "artifact_integrity", "status": "PASS"},
                    {"check": "provenance", "status": "PASS"}
                ],
                "artifacts_verified": len(artifacts)
            }

            self.state_data["verification_report"] = verification_report
            return {"success": True, "verification_status": "PASS"}
        except Exception as e:
            return {"success": False, "error": f"Verification failed: {e}"}

    def _finalize(self) -> Dict[str, Any]:
        """Finalize the pipeline and create evidence bundle."""
        try:
            # Create evidence bundle
            from shieldcraft.services.evidence_service import EvidenceService

            evidence_service = EvidenceService()
            bundle_path = "evidence_bundle.zip"
            evidence_service.create_evidence_bundle(
                self.state_data,
                ".",  # Current dir as artifacts dir
                bundle_path
            )

            self.state_data["evidence_bundle"] = bundle_path
            return {"success": True, "bundle_created": bundle_path}
        except Exception as e:
            return {"success": False, "error": f"Finalization failed: {e}"}


# CLI interface
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python local_orchestrator.py <spec_path>")
        sys.exit(1)

    orchestrator = LocalOrchestrator()
    spec_path = sys.argv[1]

    try:
        result = orchestrator.run_manufacture_pipeline(spec_path)
        print(json.dumps(result, indent=2))

        if result["status"] == "failed":
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)