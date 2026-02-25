#!/bin/bash
# Run evaluation for agents with different models and configurations
#
# You need to run `docker compose up` before running this script; see README.md for details.
#
# Docker services and ports:
#   sonnet (9100), sonnet-plugin (9101), opus (9102), opus-plugin (9103)

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_ROOT"
START=$SECONDS

for with_plugin in "False" "True"; do
    for model in "sonnet" "opus"; do
        echo ""
        echo -e "\033[1;36m========================================\033[0m"
        echo -e "\033[1;36m  Model:  $model\033[0m"
        echo -e "\033[1;36m  Plugin: $with_plugin\033[0m"
        echo -e "\033[1;36m========================================\033[0m"
        eval_start=$SECONDS
        inspect eval eval/agent/starsim.py --model anthropic/claude-${model}-4-6 --temperature 0 -T model=$model -T with_plugin=$with_plugin
        echo "Done in $(( SECONDS - eval_start )) seconds"
    done
done

elapsed=$(( SECONDS - START ))
echo ""
echo -e "\033[1;32mAll evaluations complete: $(( elapsed / 60 ))m $(( elapsed % 60 ))s\033[0m"
