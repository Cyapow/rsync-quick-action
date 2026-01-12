#!/usr/bin/env bash
set -euo pipefail

WORKFLOW_NAME="Rsync Quick Action.workflow"
TARGET_PATH="${HOME}/Library/Services/${WORKFLOW_NAME}"

if [ -d "${TARGET_PATH}" ]; then
  rm -rf "${TARGET_PATH}"
  echo "Removed ${TARGET_PATH}"
else
  echo "No Quick Action found at ${TARGET_PATH}"
fi
