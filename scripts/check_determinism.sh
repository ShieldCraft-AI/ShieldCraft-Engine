#!/bin/bash
set -e

SPEC_FILE="spec/se_dsl_v1.spec.json"
OUTPUT_DIR="artifacts/determinism"

mkdir -p "$OUTPUT_DIR"

# Run canonical JSON serializer twice
python -c "
import json
from shieldcraft.util.json_canonicalizer import canonicalize

with open('$SPEC_FILE') as f:
    spec = json.load(f)

canonical1 = canonicalize(json.dumps(spec))
canonical2 = canonicalize(json.dumps(spec))

with open('$OUTPUT_DIR/run1.json', 'w') as f:
    f.write(canonical1)

with open('$OUTPUT_DIR/run2.json', 'w') as f:
    f.write(canonical2)
"

# Compute sha256 hashes
HASH1=$(sha256sum "$OUTPUT_DIR/run1.json" | awk '{print $1}')
HASH2=$(sha256sum "$OUTPUT_DIR/run2.json" | awk '{print $1}')

echo "Run 1 hash: $HASH1" > "$OUTPUT_DIR/check.txt"
echo "Run 2 hash: $HASH2" >> "$OUTPUT_DIR/check.txt"

if [ "$HASH1" != "$HASH2" ]; then
    echo "FAIL: Hashes differ" >> "$OUTPUT_DIR/check.txt"
    echo "ERROR: Determinism check failed - hashes differ"
    cat "$OUTPUT_DIR/check.txt"
    exit 1
fi

echo "PASS: Hashes match" >> "$OUTPUT_DIR/check.txt"
echo "Determinism check passed"
cat "$OUTPUT_DIR/check.txt"
exit 0
