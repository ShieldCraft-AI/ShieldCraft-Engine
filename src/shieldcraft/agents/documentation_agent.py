"""
Documentation Agent for ShieldCraft Engine.
Generates product and code documentation from spec and artifacts.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any
from shieldcraft.services.spec.ingestion import ingest_spec


class DocumentationAgent:
    """
    Agent that generates documentation from specs and code artifacts.
    """

    def __init__(self):
        self.id = "documentation_agent.v1"
        self.description = "Generates product + code documentation from spec and code artifacts."

    def generate_docs(self, spec_path: str, artifacts_dir: str = None) -> Dict[str, Any]:
        """
        Generate documentation manifest.

        Args:
            spec_path: Path to the spec file
            artifacts_dir: Optional directory with generated artifacts

        Returns:
            Documentation manifest dict
        """
        # Load spec
        spec_data = ingest_spec(spec_path)
        if not isinstance(spec_data, dict):
            raise ValueError("Spec must be structured data")

        # Generate product docs
        product_docs = self._generate_product_docs(spec_data)

        # Generate code docs if artifacts available
        code_docs = {}
        if artifacts_dir and Path(artifacts_dir).exists():
            code_docs = self._generate_code_docs(artifacts_dir)

        # Create manifest
        manifest = {
            "agent_id": self.id,
            "spec_hash": self._compute_hash(spec_data),
            "generated_at": "2025-12-23T00:00:00Z",  # Would use datetime
            "product_documentation": product_docs,
            "code_documentation": code_docs,
            "format": "markdown",
            "provenance": {
                "input_spec": spec_path,
                "artifacts_dir": artifacts_dir
            }
        }

        return manifest

    def _generate_product_docs(self, spec: Dict[str, Any]) -> Dict[str, str]:
        """Generate product documentation from spec."""
        docs = {}

        # README.md
        docs["README.md"] = f"""# {spec.get('product_name', 'ShieldCraft Engine')}

{spec.get('summary', 'A deterministic AI software manufacturing platform.')}

## Overview

{self._extract_section(spec, 'why_now', 'summary')}

## Features

{self._extract_features(spec)}

## Installation

TODO: Add installation instructions.

## Usage

TODO: Add usage examples.

## Architecture

{self._extract_section(spec, 'architecture', 'overview')}
"""

        # API docs
        if 'api' in spec:
            docs["API.md"] = self._generate_api_docs(spec['api'])

        return docs

    def _generate_code_docs(self, artifacts_dir: str) -> Dict[str, str]:
        """Generate code documentation from artifacts."""
        docs = {}
        artifacts_path = Path(artifacts_dir)

        # Generate docs for generated code
        if (artifacts_path / "src").exists():
            docs["CODE.md"] = self._generate_code_overview(artifacts_path / "src")

        return docs

    def _extract_section(self, spec: Dict, key: str, subkey: str = None) -> str:
        """Extract text from spec section."""
        section = spec.get(key, {})
        if subkey:
            return section.get(subkey, "Not specified")
        return str(section)

    def _extract_features(self, spec: Dict) -> str:
        """Extract features from differentiators."""
        differentiators = spec.get('technical_differentiators', {}).get('table', '')
        return f"Key differentiators:\n{differentiators}"

    def _generate_api_docs(self, api_spec: Dict) -> str:
        """Generate API documentation."""
        docs = "# API Documentation\n\n"

        for endpoint in api_spec.get('endpoints', []):
            docs += f"## {endpoint['id']}\n\n"
            docs += f"**Path:** {endpoint['path']}\n\n"
            docs += f"**Method:** {endpoint['method']}\n\n"
            docs += f"**Summary:** {endpoint['summary']}\n\n"

        return docs

    def _generate_code_overview(self, src_dir: Path) -> str:
        """Generate code overview."""
        docs = "# Code Overview\n\n"

        # List generated modules
        if src_dir.exists():
            docs += "## Generated Modules\n\n"
            for py_file in src_dir.rglob("*.py"):
                docs += f"- {py_file.relative_to(src_dir)}\n"

        return docs

    def _compute_hash(self, data: Dict) -> str:
        """Compute simple hash for provenance."""
        import hashlib
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


# CLI interface for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python documentation_agent.py <spec_path> [artifacts_dir]")
        sys.exit(1)

    agent = DocumentationAgent()
    spec_path = sys.argv[1]
    artifacts_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        manifest = agent.generate_docs(spec_path, artifacts_dir)
        print(json.dumps(manifest, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)