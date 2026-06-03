# Contributing

Thanks for your interest in contributing to the Starsim AI Evaluation project!


## Development setup

1. **Clone the repo** (with submodules):

   ```bash
   git clone --recurse-submodules https://github.com/starsimhub/scipy2026_starsim_ai.git
   cd scipy2026_starsim_ai
   ```

2. **Install dependencies** with [UV](https://docs.astral.sh/uv/):

   ```bash
   uv sync
   ```

3. **Create a `.env` file** in the repo root with your API keys (see `.env.example`).


## Running tests

Tests that don't require LLM API keys:

```bash
uv run pytest -m "not uses_llm" -v
```

All tests (requires `ANTHROPIC_API_KEY`):

```bash
uv run pytest -v
```


## Editing evaluation problems

Problem definitions live in Markdown files (`problems/starsim_t*.md`). The JSONL files are generated from these and must stay in sync:

1. Edit the `.md` file in `problems/`.
2. Regenerate JSONL:
   ```bash
   python3 problems/build_jsonl.py
   ```
3. Run tests to verify:
   ```bash
   uv run pytest -m "not uses_llm" -v
   ```


## Submitting changes

1. Create a feature branch from `main`.
2. Make your changes and ensure tests pass.
3. Open a pull request against `main`.

CI runs automatically on every PR and checks that `uv run pytest -m "not uses_llm" -v` passes.


## Code style

- **Python 3.12+**
- **Package manager:** UV (`uv sync`, `uv run`)
- Use `@pytest.mark.uses_llm` for any test that requires an API key.
