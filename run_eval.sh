#!/bin/bash
# Run all evaluations (prompt + agent)
#
# Requires: docker compose up --build  (for agent evals)
# See README.md for details.

set -e
export REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo -e "\033[1;35m=== Agent evaluations ===\033[0m"
"$REPO_ROOT/eval/agent/run.sh"
