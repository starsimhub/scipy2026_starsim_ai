#!/bin/bash
cd "$(dirname "$0")/../.." # go to root directory
inspect eval eval/llm/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0
inspect eval eval/llm/starsim.py --model anthropic/claude-opus-4-6 --temperature 0
inspect eval eval/llm/starsim.py --model openai/gpt-5-mini-2025-08-07
inspect eval eval/llm/starsim.py --model openai/gpt-5.2-2025-12-11 