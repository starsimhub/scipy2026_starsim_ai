# SciPy 2026: Starsim AI Evaluation

**How well can AI coding agents use a real scientific library?** This [SciPy 2026](https://www.scipy2026.scipy.org/) project measures that for [Starsim](https://github.com/starsimhub/starsim), an agent-based disease modeling library used to inform public health and epidemic-response decisions. Disease-modeling expertise is scarce — especially in the low- and middle-income countries where outbreaks hit hardest — so agents that can build correct, idiomatic Starsim models could meaningfully lower the barrier to rigorous epidemiological analysis.

This repository evaluates the performance of LLMs (Claude Sonnet and Opus) for understanding and building Starsim models, with and without the [Starsim AI plugin](https://github.com/starsimhub/starsim_ai). It scores agents not just on whether their code runs, but on whether it genuinely *uses Starsim as a library* rather than reinventing it.

📖 **Full documentation:** <https://starsimhub.github.io/scipy2026_starsim_ai/>


## Documentation

| Page | What it covers |
|------|----------------|
| [Getting started](docs/getting-started.md) | Step-by-step: install, start a server, run your first problem. |
| [Evaluation dataset](docs/evaluation.md) | What the benchmark measures, problem structure, scoring, and modes. |
| [Architecture](docs/architecture.md) | How the A2A server and executor are built. |
| [Execution logging](docs/execution-logging.md) | Structured JSONL logs and how to read them. |
| [Changelog](CHANGELOG.md) | Notable changes to the project. |
| [Contributing](CONTRIBUTING.md) | Dev setup, tests, problem-editing workflow, PR process. |

These pages also render as a searchable site with a full API reference at **[starsimhub.github.io/scipy2026_starsim_ai](https://starsimhub.github.io/scipy2026_starsim_ai/)**.


## Quick start

1. Install packages and set up `.env`
2. `./docker_up.sh` (start the Claude A2A servers that run the evaluation)
3. `./run_eval.sh` (run the evaluation against different models + configurations)

New to the project? Follow the [Getting started tutorial](docs/getting-started.md) for a guided walkthrough.


## Full setup

This repo uses a **git submodule** for the Starsim plugin. Clone with:

```bash
git clone --recurse-submodules https://github.com/starsimhub/scipy2026_starsim_ai.git
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule init && git submodule update
```

### Environment variables

Create a `.env` file in the repo root (loaded automatically via `python-dotenv`):

```env
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
CLAUDE_MODEL=claude-opus-4-6
VERBOSE=true
MAX_TURNS=10
LOG_DIR=/home/agent/agent_logs
```

Only the Anthropic API key is strictly required. The OpenAI key is needed for evaluation comparison.

### Installation

```bash
# Using uv
uv sync

# Or using pip
pip install -e .
```

You also need to have Docker installed for the A2A server, but the chances that you're reading this sentence and don't already have it installed seem pretty slim.


## A2A Server

The recommended way to run the Claude Code A2A server is with Docker, which provides filesystem isolation and a reproducible environment.

### Using Docker (recommended)

Docker Compose defines four services:

| Service | Port | Model | Plugin |
|---------|------|-------|--------|
| `sonnet` | 9100 | claude-sonnet-4-6 | No |
| `sonnet-plugin` | 9101 | claude-sonnet-4-6 | Yes (Starsim) |
| `opus` | 9102 | claude-opus-4-6 | No |
| `opus-plugin` | 9103 | claude-opus-4-6 | Yes (Starsim) |

```bash
# Start all services
docker compose up --build

# Start only sonnet (no plugin)
docker compose up --build sonnet

# Supply API key directly (if not using .env)
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY docker compose up --build
```

Agent cards are served at `http://localhost:<port>/.well-known/agent.json`.

Docker environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Anthropic API key |
| `OPENAI_API_KEY` | — | OpenAI API key; required for running OpenAI evaluation |
| `CLAUDE_MODEL` | — | Claude model to use |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `9100` | Listen port |
| `MAX_TURNS` | — | Max agent loop iterations |
| `VERBOSE` | — | Set to `true` or `1` to enable verbose logging |
| `LOG_DIR` | `/home/agent/agent_logs` | Directory for structured execution logs |
| `RUN_ID` | ISO-8601 timestamp | Label for this server run (subdirectory under `LOG_DIR`) |
| `PLUGIN_DIRS` | — | Comma-separated plugin directory paths (set automatically for plugin services) |

### Running locally (development only)

**Not appropriate for evaluation** — the agent can access local files including problems and answers.

```bash
start-claude-code-server --port 9100 --workspace ./workspaces
```

Server CLI options:

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `9100` | Listen port |
| `--workspace` | temp dir | Root directory for per-task workspaces |
| `--model` | — | Claude model to use (also via `CLAUDE_MODEL` env var) |
| `--max-turns` | — | Max agent loop iterations |
| `--mcp` | — | MCP servers to enable (repeatable) |
| `--verbose` | off | Print detailed execution progress to stdout |
| `--log-dir` | — | Directory for structured JSONL execution logs (one file per task) |
| `--run-id` | ISO-8601 timestamp | Label for this server run (subdirectory under `--log-dir`) |

See [Architecture](docs/architecture.md) for how the server and executor work, and [Execution logging](docs/execution-logging.md) for the log format.


## Running the evaluation

The evaluation benchmark uses [inspect-ai](https://inspect.ai-safety-institute.org.uk/) to measure performance on the Starsim problem set. See [`eval/prompt/README.md`](eval/prompt/README.md) for the full list of options, and [Evaluation dataset](docs/evaluation.md) for what the benchmark measures and how it's scored.

### Agent evaluation (iterative)

Tests an agent's ability to iteratively write, test, and debug Starsim code. Problems are sent to the Claude Code A2A server, which can execute code, observe errors, and refine its solution.

```bash
# Sonnet (no plugin → port 9100)
inspect eval eval/agent/starsim.py -T model=sonnet

# Sonnet + plugin (→ port 9101)
inspect eval eval/agent/starsim.py -T model=sonnet -T with_plugin=True

# Opus (no plugin → port 9102)
inspect eval eval/agent/starsim.py -T model=opus

# Single tutorial
inspect eval eval/agent/starsim.py -T model=sonnet -T tutorial=starsim_t1

# Customize timeouts and retries
inspect eval eval/agent/starsim.py -T model=sonnet -T request_timeout=300 -T max_retries=5
```

Agent evaluation parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model` | `sonnet` | Agent model: `sonnet` or `opus` (determines A2A server port) |
| `problems_dir` | `./problems` | Path to problem JSONL directory |
| `tutorial` | all | Run only a specific tutorial (e.g. `starsim_t1`) |
| `with_background` | `True` | Include background context in prompts |
| `with_test_cases` | `True` | Include test cases in prompts |
| `with_plugin` | `False` | Use the plugin-enabled server variant |
| `timeout` | `60` | Timeout in seconds for each test case execution |
| `request_timeout` | `600` | HTTP timeout in seconds for agent requests |
| `max_retries` | `1` | Max retries on HTTP timeout |

### Prompt evaluation (one-shot)

Tests a model's ability to generate correct Starsim code in a single attempt (no A2A server needed):

```bash
# Sonnet
inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0

# Single tutorial
inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0 -T tutorial=starsim_t1

# Without background context
inspect eval eval/prompt/starsim.py --model openai/gpt-5-mini-2025-08-07 -T with_background=False

# Run all models (~10 min)
./eval/prompt/run.sh
```

### Analysis

```bash
uv run python -i analysis/eval_performance.py
```


## Evaluation dataset

Our benchmark follows the structure of [SciCode](https://arxiv.org/abs/2407.13168), adapted for disease modeling with Starsim. It rewards agents that can **leverage Starsim as a library** — not just produce correct numerical output — using an LLM-judge assessment alongside test-case validation.

Browse the problems interactively:

```bash
uv run streamlit run problems/app.py
```

Edit problems in the Markdown sources (`problems/starsim_t*.md`), then regenerate the JSONL:

```bash
python3 problems/build_jsonl.py
```

👉 See [**Evaluation dataset**](docs/evaluation.md) for the full picture: problem structure and fields, the SciCode-derived evaluation modes, scoring criteria, and the problem domains covered.


## Project structure

| Directory | Purpose |
|-----------|---------|
| `claude_a2a/` | Python package: A2A HTTP server + Claude Agent SDK bridge |
| `eval/` | Evaluation harness ([inspect-ai](https://inspect.ai-safety-institute.org.uk/)): prompt and agent benchmarks |
| `problems/` | Evaluation dataset (Markdown source + generated JSONL) and Streamlit browser |
| `analysis/` | Post-evaluation analysis scripts and plotting |
| `tests/` | pytest test suite |
| `starsim_ai/` | Git submodule: [Starsim AI plugin](https://github.com/starsimhub/starsim_ai) (mounted into Docker for plugin-enabled agents) |
| `logs/` | Evaluation run logs (`.eval` files, gitignored) |

For the design of the A2A server and executor, see [**Architecture**](docs/architecture.md).


## Running tests

```bash
uv run pytest tests/
```

- `test_problems.py` — Validates problem JSONL schema and runs gold solutions against their test cases.
- `test_claude_code_exector.py` — Tests A2A server: agent discovery, one-shot requests, and multi-turn conversations.
