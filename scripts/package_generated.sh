#!/bin/bash
# Package generated outputs into deterministic tar.gz

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <fingerprint>"
  echo "Packages .selfhost_outputs/{fingerprint}/modules/ into dist/{fingerprint}.tar.gz"
  exit 1
fi

FINGERPRINT="$1"
SOURCE_DIR=".selfhost_outputs/${FINGERPRINT}/modules"
OUTPUT_DIR="dist"
OUTPUT_FILE="${OUTPUT_DIR}/${FINGERPRINT}.tar.gz"

# Check source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: Source directory $SOURCE_DIR not found"
  exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Package with deterministic ordering
# - Sort files by name
# - Use --mtime to set consistent timestamp
# - Use --owner/--group for consistent metadata
echo "Packaging $SOURCE_DIR -> $OUTPUT_FILE"

tar \
  --create \
  --gzip \
  --file "$OUTPUT_FILE" \
  --directory "$SOURCE_DIR" \
  --sort=name \
  --mtime='2024-01-01 00:00:00' \
  --owner=0 \
  --group=0 \
  --numeric-owner \
  .

echo "Package created: $OUTPUT_FILE"
echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo "SHA256: $(sha256sum "$OUTPUT_FILE" | cut -d' ' -f1)"
