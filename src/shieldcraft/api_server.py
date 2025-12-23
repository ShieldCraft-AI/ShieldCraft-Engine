"""
ShieldCraft Engine API Server
Local implementation of the manufacture API endpoints.
"""

from flask import Flask, request, jsonify
import json
import uuid
from datetime import datetime
from pathlib import Path
import os

app = Flask(__name__)

# In-memory storage for demo (would be database in production)
runs = {}

@app.route('/api/v1/manufacture', methods=['POST'])
def manufacture():
    """Submit spec to manufacture artifacts."""
    try:
        data = request.get_json()
        if not data or 'spec_source' not in data:
            return jsonify({"code": "INVALID_REQUEST", "message": "Missing spec_source"}), 400

        # Generate run ID
        run_id = str(uuid.uuid4())

        # Store run data
        runs[run_id] = {
            "id": run_id,
            "status": "accepted",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "spec": data,
            "result": None
        }

        # In real implementation, this would enqueue the job
        # For demo, simulate immediate processing
        if data.get('run_options', {}).get('dry_run', False):
            # Simulate dry run
            runs[run_id]["status"] = "completed"
            runs[run_id]["result"] = {
                "artifacts": ["preview.json"],
                "evidence_bundle": "evidence_bundle.zip"
            }

        response = {
            "code": "RUN_ACCEPTED",
            "message": "Run queued successfully",
            "run_id": run_id,
            "status_url": f"/api/v1/runs/{run_id}/status"
        }

        return jsonify(response), 202

    except Exception as e:
        return jsonify({"code": "INTERNAL_ERROR", "message": str(e)}), 500

@app.route('/api/v1/runs/<run_id>/status', methods=['GET'])
def get_run_status(run_id):
    """Get run status."""
    if run_id not in runs:
        return jsonify({"code": "RUN_NOT_FOUND", "message": "Run not found"}), 404

    run = runs[run_id]
    return jsonify({
        "run_id": run_id,
        "status": run["status"],
        "created_at": run["created_at"],
        "completed_at": run.get("completed_at"),
        "result": run.get("result")
    })

@app.route('/api/v1/runs/<run_id>/artifacts/<artifact_id>', methods=['GET'])
def get_artifact(run_id, artifact_id):
    """Get specific artifact."""
    if run_id not in runs:
        return jsonify({"code": "RUN_NOT_FOUND", "message": "Run not found"}), 404

    run = runs[run_id]
    if run["status"] != "completed":
        return jsonify({"code": "RUN_NOT_COMPLETED", "message": "Run not completed"}), 409

    # In real implementation, serve the actual file
    # For demo, return mock data
    if artifact_id == "preview.json":
        return jsonify({"mock": "artifact_data"}), 200
    elif artifact_id == "evidence_bundle.zip":
        return jsonify({"mock": "bundle_data"}), 200
    else:
        return jsonify({"code": "ARTIFACT_NOT_FOUND", "message": "Artifact not found"}), 404

@app.route('/api/v1/runs/<run_id>/evidence', methods=['GET'])
def get_evidence(run_id):
    """Get evidence bundle."""
    if run_id not in runs:
        return jsonify({"code": "RUN_NOT_FOUND", "message": "Run not found"}), 404

    run = runs[run_id]
    if run["status"] != "completed":
        return jsonify({"code": "RUN_NOT_COMPLETED", "message": "Run not completed"}), 409

    # Mock evidence bundle
    return jsonify({
        "bundle_id": f"bundle_{run_id}",
        "signature": "mock_signature",
        "artifacts": ["preview.json"]
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "version": "1.0.0"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)