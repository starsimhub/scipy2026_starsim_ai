# SciPy 2026: Starsim AI Evaluation

## Introduction

Submission for [SciPy 2026](https://pretalx.com/scipy-2026/cfp) evaluating Starsim-AI.

Deadline: **February 25, 2026**

Track: **Data-Driven Discovery, Machine Learning and Artificial Intelligence**

> This track aims to bring together the latest advances in Artificial Intelligence and Machine Learning (AI/ML) and areas of data-driven insights that focus on advancing novel discovery across fields and applications in science and industry. This includes the development and application of new and existing open-source tools and techniques that have been influential in advancing scientific progress. **We encourage submissions that include stories of applications and improvements to simulation and simulation-based inference.**

## Proposal

- Build a Claude Code plugin for Starsim that combines MCP servers for Starsim + individual models and general skills (e.g., a disease modeling expert subagent, a code quality subagent)
- Write an exam to test Starsim skills/knowledge
- Evaluate how well the enhanced AI performs compared to out-of-the-box versions on the exam

## Evaluation Dataset

Our evaluation benchmark follows the structure of [SciCode](https://arxiv.org/abs/2407.13168), adapted for disease modeling with [Starsim](https://github.com/starsimhub/starsim). A central goal of this benchmark is to measure how well an agent can **leverage Starsim as a library** to solve modeling problems, rather than writing disease models from scratch. Agents that effectively use Starsim's built-in components (e.g., `ss.SIR`, `ss.Vaccine`, contact networks) demonstrate the kind of library fluency that matters in practice.

To assess this, we depart from SciCode in one key way: in addition to test-case validation, we use an **LLM-judge assessment** to evaluate whether the agent's solution actually uses Starsim APIs. This catches cases where an agent produces numerically correct output but bypasses Starsim entirely (e.g., by implementing ODE solvers from scratch). The judge reviews the generated code and scores it on Starsim API usage, idiomatic patterns, and appropriate use of library abstractions.

### Problem Structure

Each problem is a multi-step disease modeling task. The **source of truth** is a set of human-readable Markdown files (`problems/starsim_t*.md`). These are converted to JSONL (`problems/starsim_t*.jsonl`) for consumption by the evaluation harness.

**Editing problems:** Edit the `.md` files, then regenerate the JSONL:

```bash
python3 problems/build_jsonl.py
```

A test (`test_jsonl_matches_markdown`) ensures the JSONL files stay in sync with the Markdown sources — if you edit a `.md` file without regenerating, `uv run pytest tests/test_problems.py` will fail.

Problems are organized hierarchically:

**Main Problem** — A complete modeling task (e.g., "Build an SIR model with age-stratified mixing and calibrate to observed data").

Each main problem decomposes into sequential **subproblems**, where later steps can depend on outputs from earlier ones.

#### Fields per subproblem

| Field | Description |
|---|---|
| `problem_id` | Unique identifier for the main problem (e.g., `"starsim_01"`) |
| `sub_step_id` | Identifier for the subproblem (e.g., `"starsim_01.3"`) |
| `description` | Natural language description of the task |
| `function_header` | Python function signature to implement |
| `docstring` | Input/output specification |
| `background` | Optional domain context (epidemiology concepts, model equations, parameter definitions) |
| `dependencies` | Allowed Python packages (e.g., `starsim`, `numpy`, `scipy`, `matplotlib`) |
| `test_cases` | Input-output pairs and domain-specific validations |
| `gold_solution` | Reference implementation |

### Example problem outline

```
Problem: starsim_01 — "SIR model with vaccination campaign"
  ├── Sub 1: Define disease parameters and create an SIR model
  ├── Sub 2: Add age-stratified contact network
  ├── Sub 3: Implement a time-varying vaccination intervention
  ├── Sub 4: Run the simulation and extract results
  └── Sub 5: Plot epidemic curves and compute final size
```

### Evaluation Modes

Following SciCode, we support multiple evaluation configurations:

| Mode | Background provided? | Prior solutions | Tests |
|---|---|---|---|
| **Standard** | No | Model-generated | Measures real-world capability |
| **With background** | Yes | Model-generated | Measures instruction-following |
| **Gold prior** | No | Gold solutions | Isolates per-step capability |
| **With background + gold prior** | Yes | Gold solutions | Easiest setting |

### Evaluation Criteria

Each solution is assessed on two axes:

1. **Correctness** — Does the solution pass the test cases? (Same as SciCode.)
2. **Starsim utilization** — Does the solution use Starsim effectively? An LLM judge reviews the generated code and scores it on:
   - Whether core Starsim APIs are used (e.g., `ss.Sim`, `ss.SIR`, `ss.Network`)
   - Whether library abstractions are used appropriately (e.g., using `ss.Vaccine` instead of manually modifying susceptibility)
   - Whether the code follows idiomatic Starsim patterns

A solution that passes all test cases but doesn't use Starsim would score high on correctness but low on utilization. The benchmark is designed to reward agents that can learn and apply a domain library, not just produce correct numerical output.

### Problem Domains

Problems span core Starsim use cases:

- **Basic modeling** — SIR/SIS/SEIR dynamics, parameter configuration
- **Demographics** — Birth/death processes, age structure, population networks
- **Interventions** — Vaccination campaigns, treatment protocols, behavioral changes
- **Calibration** — Fitting models to observed data, likelihood-based calibration
- **Analysis** — Result extraction, plotting, sensitivity analysis
- **Multi-disease** — Co-circulating pathogens, disease interactions
- **Advanced networks** — Household structure, spatial mixing, dynamic contact patterns

## Talk plan
- Intro to the problem (getting up to speed on a complex library) and Starsim
- How we developed the Starsim exam, and what worked well and didn't
- Describe which skills/subagents we developed and why
- Models and skillsets we tested
- Evaluation of each combination
- Open-source "gym" for users to plug in their own library, skills, and exam

## Architecture

### Claude Code A2A Server

The project includes an [A2A](https://google.github.io/A2A/) (Agent-to-Agent) server that exposes Claude Code as a discoverable, callable coding agent over HTTP.

**Server** (`src/ssai/claude_code_server.py`): Builds an Agent Card advertising four skills — code generation, code review & bug fixing, shell & DevOps, and research & exploration — and serves it via a Starlette/Uvicorn application. Configuration options:

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `9100` | Listen port |
| `--workspace` | parent dir | Root directory for per-task workspaces |
| `--model` | — | Claude model to use |
| `--max-turns` | — | Max agent loop iterations |
| `--mcp` | — | MCP servers to enable (repeatable) |

**Executor** (`src/ssai/claude_code_executor.py`): Bridges the A2A protocol to Claude Code via the Claude Agent SDK. Key behaviors:

- **Workspace isolation** — each A2A task gets its own workspace directory for file operations.
- **Multi-turn sessions** — tracks Claude Agent SDK session IDs per task so follow-up messages resume the same conversation context.
- **Streaming progress** — emits intermediate `TaskStatusUpdateEvent`s as Claude works, including text output and tool-use notifications.
- **Cancellation** — supports async cancellation via `asyncio.Event`.
- **Configurable tools** — defaults to Read, Write, Edit, MultiEdit, Bash, Glob, Grep, and WebSearch; runs with `bypassPermissions` mode.
- **MCP extensibility** — pluggable MCP servers for domain-specific capabilities (an example "secret" server is included in `src/ssai/mcp_secret.py`).

### Running the server

```bash
# Install dependencies
uv sync

# Start the server
start-claude-code-server --port 9100 --workspace ./workspaces
```

The agent card is served at `http://localhost:9100/.well-known/agent.json`.

### Browsing the evaluation dataset

A Streamlit app (`app.py`) lets you browse the evaluation problems interactively.

```bash
uv run streamlit run app.py
```

Features:
- Select a main problem (Tutorial 1, 2, or 3) from the sidebar
- Browse individual sub-steps with full descriptions, background context, function signatures, docstrings, and test cases
- Toggle **Show gold solution** to reveal the reference implementation

### Running the evaluation

The evaluation benchmark uses [inspect-ai](https://inspect.ai-safety-institute.org.uk/) to measure performance on the Starsim problem set. There are two evaluation modes: **LLM** (one-shot generation) and **Agent** (iterative via the Claude Code A2A server).

Set your API key via environment variable or a `.env` file (loaded automatically via python-dotenv). See [`eval/llm/README.md`](eval/llm/README.md) for the full list of options.

#### LLM evaluation (one-shot)

Tests a model's ability to generate correct Starsim code in a single attempt:

```bash
# Run the full benchmark
inspect eval eval/llm/starsim.py --model anthropic/claude-sonnet-4-20250514 --temperature 0

# Run a single tutorial
inspect eval eval/llm/starsim.py --model anthropic/claude-sonnet-4-20250514 --temperature 0 -T tutorial=starsim_t1

# Run without background context
inspect eval eval/llm/starsim.py --model openai/gpt-4o --temperature 0 -T with_background=False
```

#### Agent evaluation (iterative)

Tests an agent's ability to iteratively write, test, and debug Starsim code. Problems are sent to the Claude Code A2A server, which can execute code, observe errors, and refine its solution. The agent receives test cases in the prompt so it can self-test.

```bash
# Start the A2A server (or use Docker, see below)
start-claude-code-server --port 9100 --workspace ./workspaces

# Run the agent eval
inspect eval eval/agent/starsim.py -T agent_url=http://localhost:9100

# Run a single tutorial
inspect eval eval/agent/starsim.py -T agent_url=http://localhost:9100 -T tutorial=starsim_t1
```

To run the A2A server in Docker for filesystem isolation:

```bash
ANTHROPIC_API_KEY=sk-... docker compose up --build

# Specify the Claude model (defaults to the Claude Code CLI default)
ANTHROPIC_API_KEY=sk-... CLAUDE_MODEL=claude-sonnet-4-6 docker compose up --build

# Then run the eval against it
inspect eval eval/agent/starsim.py -T agent_url=http://localhost:9100
```

You can also set these in a `.env` file next to `docker-compose.yml`:

```env
ANTHROPIC_API_KEY=sk-...
CLAUDE_MODEL=claude-opus-4-6
```

### Running tests

```bash
uv run pytest tests/
```

- `test_problems.py` — Validates problem JSONL schema and runs gold solutions against their test cases.
- `test_claude_code_exector.py` — Tests A2A server: agent discovery, one-shot requests, and multi-turn conversations.