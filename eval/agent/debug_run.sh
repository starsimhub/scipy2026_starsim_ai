#!/bin/bash
# Minimal version of run.sh for debugging

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_ROOT"
START=$SECONDS

tutorial="starsim_t1"

for with_plugin in "False" "True"; do
    for model in "sonnet"; do
        if [ "$model" = "sonnet" ]; then
            base_port=9100
        else
            base_port=9102
        fi
        if [ "$with_plugin" = "True" ]; then
            port=$((base_port + 1))
        else
            port=$base_port
        fi
        agent_url="http://localhost:$port"

        echo ""
        echo -e "\033[1;36m========================================\033[0m"
        echo -e "\033[1;36m  Model:  $model\033[0m"
        echo -e "\033[1;36m  Plugin: $with_plugin\033[0m"
        echo -e "\033[1;36m  Agent:  $agent_url\033[0m"
        echo -e "\033[1;36m========================================\033[0m"
        eval_start=$SECONDS
        inspect eval eval/agent/starsim.py --model anthropic/claude-${model}-4-6 --temperature 0 -T with_plugin=$with_plugin -T agent_url=$agent_url -T tutorial=$tutorial
        echo "Done in $(( SECONDS - eval_start )) seconds"
    done
done

elapsed=$(( SECONDS - START ))
echo ""
echo -e "\033[1;32mAll evaluations complete: $(( elapsed / 60 ))m $(( elapsed % 60 ))s\033[0m"
