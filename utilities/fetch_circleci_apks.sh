#!/bin/bash
# Fetch APK artifacts from CircleCI mozilla/experimenter builds
# This script is designed for use in GitHub Actions CI

set -e

ORG="${CIRCLECI_ORG:-mozilla}"
REPO="${CIRCLECI_REPO:-experimenter}"
BRANCH="${CIRCLECI_BRANCH:-main}"
OUTPUT_DIR="${CIRCLECI_OUTPUT_DIR:-.}"
WORKFLOW_NAME="${CIRCLECI_WORKFLOW_NAME:-}"
JOB_NAME="${CIRCLECI_JOB_NAME:-}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Fetching APK artifacts from CircleCI"
echo "Organization: $ORG"
echo "Repository: $REPO"
echo "Branch: $BRANCH"
echo "Output directory: $OUTPUT_DIR"

# Check if requests library is installed
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing required Python dependencies..."
    pip3 install requests
fi

CMD="python3 $SCRIPT_DIR/get_circleci_apks.py --org $ORG --repo $REPO --branch $BRANCH --output-dir $OUTPUT_DIR"

if [ -n "$WORKFLOW_NAME" ]; then
    CMD="$CMD --workflow-name $WORKFLOW_NAME"
fi

if [ -n "$JOB_NAME" ]; then
    CMD="$CMD --job-name $JOB_NAME"
fi

eval $CMD

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✓ APK artifacts downloaded successfully"
    ls -lh "$OUTPUT_DIR"/*.apk 2>/dev/null || echo "Warning: No APK files found in output directory"
else
    echo "✗ Failed to download APK artifacts"
    exit 1
fi

exit 0
