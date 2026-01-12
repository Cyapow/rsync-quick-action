#!/usr/bin/env bash
set -euo pipefail

WORKFLOW_NAME="Rsync Quick Action.workflow"
TARGET_DIR="${HOME}/Library/Services"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_WORKFLOW="${REPO_ROOT}/quick_action/${WORKFLOW_NAME}"

if [ ! -d "${SOURCE_WORKFLOW}" ]; then
  echo "Workflow bundle not found at ${SOURCE_WORKFLOW}."
  echo "Please create the workflow using the instructions in quick_action/README.md before running this installer."
  exit 1
fi

echo "Installing Quick Action to ${TARGET_DIR}/${WORKFLOW_NAME}"
mkdir -p "${TARGET_DIR}"
cp -R "${SOURCE_WORKFLOW}" "${TARGET_DIR}/${WORKFLOW_NAME}"
echo "Done. You may need to log out/in or restart Finder for the service to appear."
