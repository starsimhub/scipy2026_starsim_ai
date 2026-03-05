#!/bin/bash
# Run analysis after evaluation has been run
# NB: best to use uv since fragile dependency issues otherwise

cd analysis && uv run eval_performance.py
