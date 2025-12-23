"""
Local Artifact Store for ShieldCraft Engine.
Simple file-based implementation (alternative to S3).
"""

import hashlib
import json
import os
from typing import Dict, Any, Optional, BinaryIO
from pathlib import Path


class LocalArtifactStore:
    """
    Local file-based artifact store for generated artifacts.
    """

    def __init__(self, storage_dir: str = ".shieldcraft_artifacts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.metadata_dir = self.storage_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)

    def store_artifact(self, run_id: str, artifact_id: str, content: bytes, metadata: Dict[str, Any]) -> bool:
        """
        Store artifact content and metadata.

        Args:
            run_id: Run identifier
            artifact_id: Artifact identifier
            content: Binary content
            metadata: Artifact metadata

        Returns:
            Success status
        """
        try:
            # Create run directory
            run_dir = self.storage_dir / run_id
            run_dir.mkdir(exist_ok=True)

            # Store content
            content_file = run_dir / f"{artifact_id}.bin"
            with open(content_file, 'wb') as f:
                f.write(content)

            # Calculate hash
            sha256_hash = hashlib.sha256(content).hexdigest()

            # Store metadata
            metadata_file = self.metadata_dir / f"{run_id}_{artifact_id}.json"
            full_metadata = {
                **metadata,
                "run_id": run_id,
                "artifact_id": artifact_id,
                "size_bytes": len(content),
                "sha256_hash": sha256_hash,
                "stored_at": "2025-12-23T00:00:00Z",
                "storage_type": "local_file"
            }

            with open(metadata_file, 'w') as f:
                json.dump(full_metadata, f, indent=2, default=str)

            return True
        except Exception:
            return False

    def retrieve_artifact(self, run_id: str, artifact_id: str) -> Optional[bytes]:
        """
        Retrieve artifact content.

        Args:
            run_id: Run identifier
            artifact_id: Artifact identifier

        Returns:
            Binary content or None if not found
        """
        try:
            run_dir = self.storage_dir / run_id
            content_file = run_dir / f"{artifact_id}.bin"
            if content_file.exists():
                with open(content_file, 'rb') as f:
                    return f.read()
        except Exception:
            pass
        return None

    def get_artifact_metadata(self, run_id: str, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get artifact metadata.

        Args:
            run_id: Run identifier
            artifact_id: Artifact identifier

        Returns:
            Metadata dict or None if not found
        """
        try:
            metadata_file = self.metadata_dir / f"{run_id}_{artifact_id}.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def list_run_artifacts(self, run_id: str) -> list:
        """
        List all artifacts for a run.

        Args:
            run_id: Run identifier

        Returns:
            List of artifact summaries
        """
        artifacts = []
        metadata_pattern = f"{run_id}_*.json"
        for metadata_file in self.metadata_dir.glob(metadata_pattern):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    artifacts.append({
                        "artifact_id": metadata["artifact_id"],
                        "type": metadata.get("type", "unknown"),
                        "size_bytes": metadata["size_bytes"],
                        "sha256_hash": metadata["sha256_hash"],
                        "stored_at": metadata["stored_at"]
                    })
            except Exception:
                continue
        return artifacts

    def delete_artifact(self, run_id: str, artifact_id: str) -> bool:
        """
        Delete artifact and its metadata.

        Args:
            run_id: Run identifier
            artifact_id: Artifact identifier

        Returns:
            Success status
        """
        try:
            # Delete content
            run_dir = self.storage_dir / run_id
            content_file = run_dir / f"{artifact_id}.bin"
            if content_file.exists():
                content_file.unlink()

            # Delete metadata
            metadata_file = self.metadata_dir / f"{run_id}_{artifact_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()

            return True
        except Exception:
            return False