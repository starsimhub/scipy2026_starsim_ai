#!/bin/bash
# Run debug evaluation for prompt and agent architectures

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"
echo `pwd`
START=$SECONDS

# prompt evaluations
inspect eval eval/prompt/starsim.py --model openai/gpt-5-mini-2025-08-07 -T with_background=False -T with_test_cases=False  -T tutorial=starsim_t1
inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0 -T with_background=False -T with_test_cases=False -T tutorial=starsim_t1

# agent evaluations (--model is required by inspect but unused; actual model
# is determined by the A2A server via -T model)
inspect eval eval/agent/starsim.py --model sonnet -T model=sonnet -T with_plugin=False -T tutorial=starsim_t1
inspect eval eval/agent/starsim.py --model sonnet -T model=sonnet -T with_plugin=True -T tutorial=starsim_t1

elapsed=$(( SECONDS - START ))
echo ""
echo -e "\033[1;32mAll evaluations complete: $(( elapsed / 60 ))m $(( elapsed % 60 ))s\033[0m"
