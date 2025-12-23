"""
Local State Store for ShieldCraft Engine.
Simple file-based implementation (alternative to DynamoDB).
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class LocalStateStore:
    """
    Local file-based state store for run state persistence.
    """

    def __init__(self, storage_dir: str = ".shieldcraft_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save_run_state(self, run_id: str, state: Dict[str, Any]) -> bool:
        """
        Save run state to local file.

        Args:
            run_id: Unique run identifier
            state: State data to persist

        Returns:
            Success status
        """
        try:
            state_file = self.storage_dir / f"{run_id}.json"
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            return True
        except Exception:
            return False

    def load_run_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Load run state from local file.

        Args:
            run_id: Unique run identifier

        Returns:
            State data or None if not found
        """
        try:
            state_file = self.storage_dir / f"{run_id}.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def list_runs(self, status_filter: Optional[str] = None) -> list:
        """
        List all runs, optionally filtered by status.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of run summaries
        """
        runs = []
        for state_file in self.storage_dir.glob("*.json"):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    if status_filter is None or state.get("status") == status_filter:
                        runs.append({
                            "run_id": state_file.stem,
                            "status": state.get("status"),
                            "created_at": state.get("created_at"),
                            "spec_id": state.get("spec", {}).get("metadata", {}).get("product_id")
                        })
            except Exception:
                continue
        return runs

    def delete_run_state(self, run_id: str) -> bool:
        """
        Delete run state file.

        Args:
            run_id: Unique run identifier

        Returns:
            Success status
        """
        try:
            state_file = self.storage_dir / f"{run_id}.json"
            if state_file.exists():
                state_file.unlink()
            return True
        except Exception:
            return False