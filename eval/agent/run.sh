#!/bin/bash
# Run evaluation for agents with different models and configurations
#
# You need to run `docker compose up` before running this script; see README.md for details.
#
# NB: Claude plugins are only available via the agent implementation,
# so this is the main use case.

cd "$(dirname "$0")/../.." # go to root directory
START=$SECONDS

models=(
    "anthropic/claude-opus-4-6 --temperature 0"
    "anthropic/claude-sonnet-4-6 --temperature 0"
    "openai/gpt-5.2-2025-12-11"
    "openai/gpt-5-mini-2025-08-07"
)

urls=(
    "http://localhost:9100"  # without plugin
    "http://localhost:9101"  # with plugin
)

for url in "${urls[@]}"; do
    for model in "${models[@]}"; do
        echo ""
        echo -e "\033[1;36m========================================\033[0m"
        echo -e "\033[1;36m  Model: $model\033[0m"
        echo -e "\033[1;36m  URL:   $url\033[0m"
        echo -e "\033[1;36m========================================\033[0m"
        eval_start=$SECONDS
        inspect eval eval/agent/starsim.py --model $model -T agent_url=$url
        echo "Done in $(( SECONDS - eval_start )) seconds"
    done
done

elapsed=$(( SECONDS - START ))
echo ""
echo -e "\033[1;32mAll evaluations complete: $(( elapsed / 60 ))m $(( elapsed % 60 ))s\033[0m"
