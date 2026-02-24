#!/bin/bash
cd "$(dirname "$0")/../.." # go to root directory
START=$SECONDS

# with background and test cases
inspect eval eval/llm/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0
inspect eval eval/llm/starsim.py --model anthropic/claude-opus-4-6 --temperature 0
inspect eval eval/llm/starsim.py --model openai/gpt-5-mini-2025-08-07
inspect eval eval/llm/starsim.py --model openai/gpt-5.2-2025-12-11 

# without background and test cases
inspect eval eval/llm/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0 -T with_background=False -T with_test_cases=False
inspect eval eval/llm/starsim.py --model anthropic/claude-opus-4-6 --temperature 0 -T with_background=False -T with_test_cases=False
inspect eval eval/llm/starsim.py --model openai/gpt-5-mini-2025-08-07 -T with_background=False -T with_test_cases=False
inspect eval eval/llm/starsim.py --model openai/gpt-5.2-2025-12-11 -T with_background=False -T with_test_cases=False

echo "Done: $(( (SECONDS - START) / 60 )) minutes"