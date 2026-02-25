#!/bin/bash
# Run analysis after evaluation has been run
# NB: only uv run works, running the script directly does not for some reason

cd analysis && uv run eval_performance.py
