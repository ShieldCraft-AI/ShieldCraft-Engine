#!/bin/bash
set -e

# Run tests
pytest -q

# On success, write success message
mkdir -p artifacts/test_failures
echo "ALL PASS" > artifacts/test_failures/summary.txt

exit 0
