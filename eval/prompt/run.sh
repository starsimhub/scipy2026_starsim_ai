#!/bin/bash
# Run prompt evaluations for all models with and without background/test cases
#
# Model shorthands → full model IDs (--model flag):
#   sonnet     → anthropic/claude-sonnet-4-6
#   opus       → anthropic/claude-opus-4-6
#   gpt-5-mini → openai/gpt-5-mini-2025-08-07
#   gpt-5.2    → openai/gpt-5.2-2025-12-11

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_ROOT"
START=$SECONDS

# with background and test cases (defaults)
inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0
inspect eval eval/prompt/starsim.py --model anthropic/claude-opus-4-6 --temperature 0
inspect eval eval/prompt/starsim.py --model openai/gpt-5-mini-2025-08-07 --temperature 0
inspect eval eval/prompt/starsim.py --model openai/gpt-5.2-2025-12-11 --temperature 0

# without background and test cases
inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0 -T with_background=False -T with_test_cases=False
inspect eval eval/prompt/starsim.py --model anthropic/claude-opus-4-6 --temperature 0 -T with_background=False -T with_test_cases=False
inspect eval eval/prompt/starsim.py --model openai/gpt-5-mini-2025-08-07 --temperature 0 -T with_background=False -T with_test_cases=False
inspect eval eval/prompt/starsim.py --model openai/gpt-5.2-2025-12-11 --temperature 0 -T with_background=False -T with_test_cases=False

elapsed=$(( SECONDS - START ))
echo ""
echo -e "\033[1;32mAll evaluations complete: $(( elapsed / 60 ))m $(( elapsed % 60 ))s\033[0m"