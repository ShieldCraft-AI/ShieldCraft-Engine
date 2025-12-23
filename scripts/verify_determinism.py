#!/usr/bin/env python3
"""
Determinism verification script for ShieldCraft Engine.
Runs the engine multiple times with the same input and verifies identical outputs.
"""

import os
import sys
import hashlib
import tempfile
import shutil
import subprocess
from pathlib import Path

def compute_directory_hash(directory):
    """Compute SHA256 hash of all files in directory recursively."""
    hash_obj = hashlib.sha256()
    for root, dirs, files in os.walk(directory):
        dirs.sort()  # Ensure deterministic traversal
        for file in sorted(files):
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                hash_obj.update(f.read())
    return hash_obj.hexdigest()

def run_engine(spec_path, output_dir):
    """Run the engine with given spec and output to directory."""
    cmd = [sys.executable, 'src/shieldcraft/main.py', '--spec', spec_path, '--dry-run', '--emit-preview', str(output_dir / 'preview.json')]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/../')
    return result.returncode == 0, result.stdout, result.stderr

def verify_determinism(spec_path, runs=3):
    """Run engine multiple times and verify determinism."""
    temp_dirs = []
    hashes = []

    for i in range(runs):
        temp_dir = Path(tempfile.mkdtemp())
        temp_dirs.append(temp_dir)

        success, stdout, stderr = run_engine(spec_path, temp_dir)
        if not success:
            print(f"Run {i+1} failed:")
            print(stdout)
            print(stderr)
            return False

        # Compute hash of outputs
        output_hash = compute_directory_hash(temp_dir)
        hashes.append(output_hash)
        print(f"Run {i+1} hash: {output_hash}")

    # Check all hashes are identical
    if len(set(hashes)) == 1:
        print(f"✓ Determinism verified: {runs} runs produced identical outputs (hash: {hashes[0]})")
        return True
    else:
        print("✗ Determinism failed: Outputs differ between runs")
        for i, h in enumerate(hashes):
            print(f"  Run {i+1}: {h}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python verify_determinism.py <spec_path>")
        sys.exit(1)

    spec_path = sys.argv[1]
    if not os.path.exists(spec_path):
        print(f"Spec file not found: {spec_path}")
        sys.exit(1)

    success = verify_determinism(spec_path)
    sys.exit(0 if success else 1)