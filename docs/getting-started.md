# Getting started

This tutorial walks you through your **first evaluation run** end to end: you'll
install the project, start one agent server, run a single problem through it, and
read the results. By the end you'll understand how the pieces connect and be
ready to explore the rest of the benchmark.

It should take about 15 minutes. You'll need [Docker](https://www.docker.com/),
[git](https://git-scm.com/), and an
[Anthropic API key](https://console.anthropic.com/).

!!! note "Tutorial vs. Quick start"
    The [Quick start](index.md#quick-start) in the README is a compressed command
    list for people who already know the system. This page is the slow,
    explained version — start here if it's your first time.

## Step 1 — Clone with submodules

This repo uses a git **submodule** for the Starsim AI plugin, so clone
recursively:

```bash
git clone --recurse-submodules https://github.com/starsimhub/scipy2026_starsim_ai.git
cd scipy2026_starsim_ai
```

Already cloned without `--recurse-submodules`? Pull the submodule in:

```bash
git submodule init && git submodule update
```

## Step 2 — Install dependencies

The project uses [UV](https://docs.astral.sh/uv/) for dependency management:

```bash
uv sync
```

This creates a virtual environment and installs everything pinned in
`uv.lock` — Starsim, inspect-ai, the A2A SDK, and the Claude Agent SDK.

## Step 3 — Add your API key

Create a `.env` file in the repo root (it's loaded automatically):

```env
ANTHROPIC_API_KEY=sk-ant-...
```

Only the Anthropic key is required for this tutorial. (The OpenAI key is only
needed when you compare against OpenAI models.) See `.env.example` for the full
list of supported variables.

## Step 4 — Start one agent server

The benchmark talks to a Claude Code **A2A server**. Docker Compose defines four
variants; for this tutorial start just the plain Sonnet one (no plugin), which
listens on port **9100**:

```bash
docker compose up --build sonnet
```

Leave this running in its own terminal. When it's ready you'll see it print its
agent card URL. Confirm it's alive from another terminal:

```bash
curl http://localhost:9100/.well-known/agent.json
```

You should get back a JSON **Agent Card** describing the agent's skills. That
card is built by
[`build_agent_card`][claude_a2a.claude_code_server.build_agent_card]; the server
internals are covered in [Architecture](architecture.md).

## Step 5 — Run a single problem

Now run **one** problem through the agent. The `-T tutorial=starsim_t1` option
restricts the run to the first tutorial problem so you get a fast result:

```bash
inspect eval eval/agent/starsim.py -T model=sonnet -T tutorial=starsim_t1
```

Here's what happens under the hood:

1. `inspect-ai` loads the `starsim_t1` problem from `problems/`.
2. It sends the problem description, function signature, and test cases to the
   A2A server on port 9100.
3. The agent writes a solution, runs the test cases in its workspace, and
   iterates until they pass (or it runs out of turns).
4. The harness scores the returned code against the same test cases and records
   the result.

## Step 6 — Inspect the results

inspect-ai prints a summary table when the run finishes — look for the
`sub_step_accuracy` and `test_pass_rate` metrics (defined in
[`eval/shared.py`][eval.shared.run_tests]).

For the full interactive view — prompts, the agent's code, tool calls, and per
test-case results — open the inspect viewer:

```bash
inspect view
```

It serves a local web UI reading the `.eval` log files written to `logs/`.

## What's next

- **Run the whole benchmark.** Drop the `-T tutorial=...` filter to run all
  problems, or start every server variant with `docker compose up --build` and
  use `./run_eval.sh`.
- **Try the one-shot benchmark.** No server needed:
  `inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6`.
- **Browse the dataset.** `uv run streamlit run problems/app.py` opens an
  interactive problem browser.
- **Understand the design.** Read [Evaluation dataset](evaluation.md) for what
  the benchmark measures and [Architecture](architecture.md) for how the server
  works.
