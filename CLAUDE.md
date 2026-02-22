# CLAUDE.md

## Project Overview

SciPy 2026 submission evaluating how well AI agents can use the **Starsim** disease modeling library. Includes an evaluation benchmark, a Claude Code A2A server, and a Streamlit problem browser.

## Key Commands

```bash
# Install dependencies
uv sync

# Run tests (excludes LLM-dependent tests)
uv run pytest -m "not uses_llm" -v

# Run all tests including LLM tests
uv run pytest -v

# Regenerate JSONL from problem Markdown files
python3 problems/build_jsonl.py

# Start the A2A server
start-claude-code-server --port 9100 --workspace ./workspaces

# Run LLM evaluation
inspect eval eval/llm/starsim.py --model anthropic/claude-sonnet-4-20250514 --temperature 0

# Run agent evaluation
inspect eval eval/agent/starsim.py -T agent_url=http://localhost:9100

# Browse problems interactively
uv run streamlit run app.py
```

## Project Structure

- `src/ssai/` — Main source package
  - `claude_code_server.py` — A2A HTTP server exposing Claude Code
  - `claude_code_executor.py` — Bridges A2A protocol to Claude Agent SDK
  - `mcp_secret.py` — Example MCP server
- `eval/` — Evaluation harness
  - `llm/starsim.py` — One-shot LLM evaluation (inspect-ai)
  - `agent/starsim.py` — Iterative agent evaluation via A2A server
  - `shared.py` — Shared evaluation utilities
- `problems/` — Problem definitions
  - `starsim_t*.md` — Source of truth (Markdown)
  - `starsim_t*.jsonl` — Generated from Markdown via `build_jsonl.py`
- `tests/` — pytest test suite
- `app.py` — Streamlit problem browser
- `Dockerfile` / `docker-compose.yml` — Containerized A2A server

## Conventions

- **Package manager:** UV (`uv sync`, `uv run`)
- **Python:** 3.12+
- **Source module:** `ssai` (mapped from `src/ssai/` via `uv_build`)
- **Problem editing:** Always edit `.md` files, then run `python3 problems/build_jsonl.py` to regenerate JSONL. Tests will fail if they're out of sync.
- **Test markers:** `@pytest.mark.uses_llm` for tests requiring API keys. CI runs `pytest -m "not uses_llm"`.
- **CI:** GitHub Actions on push/PR to `main` — runs `uv sync --dev` then `uv run pytest -m "not uses_llm" -v`
