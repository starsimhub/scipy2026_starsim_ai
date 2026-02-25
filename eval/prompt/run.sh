#!/bin/bash
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_ROOT"
START=$SECONDS

# with background and test cases
inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0
inspect eval eval/prompt/starsim.py --model anthropic/claude-opus-4-6 --temperature 0
inspect eval eval/prompt/starsim.py --model openai/gpt-5-mini-2025-08-07
inspect eval eval/prompt/starsim.py --model openai/gpt-5.2-2025-12-11 

# without background and test cases
inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0 -T with_background=False -T with_test_cases=False
inspect eval eval/prompt/starsim.py --model anthropic/claude-opus-4-6 --temperature 0 -T with_background=False -T with_test_cases=False
inspect eval eval/prompt/starsim.py --model openai/gpt-5-mini-2025-08-07 -T with_background=False -T with_test_cases=False
inspect eval eval/prompt/starsim.py --model openai/gpt-5.2-2025-12-11 -T with_background=False -T with_test_cases=False

echo "Done: $(( (SECONDS - START) / 60 )) minutes"