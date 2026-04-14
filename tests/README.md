# tests

pytest test suite for the Starsim AI Evaluation project.

## Test files

| File | What it tests |
|------|---------------|
| `test_problems.py` | Validates that problem Markdown files and generated JSONL files are in sync and well-formed. |
| `test_claude_code_exector.py` | Tests for the Claude Code executor and A2A integration. Marked with `@pytest.mark.uses_llm`. |

## Running tests

```bash
# Fast tests only (no API keys needed) -- used by CI
uv run pytest -m "not uses_llm" -v

# All tests (requires ANTHROPIC_API_KEY)
uv run pytest -v
```
