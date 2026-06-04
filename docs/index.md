# SciPy 2026: Starsim AI Evaluation

**How well can AI coding agents use a real scientific library?** This project, a
[SciPy 2026](https://www.scipy2026.scipy.org/) submission, answers that question
for [Starsim](https://github.com/starsimhub/starsim) — an agent-based disease
modeling library used to inform public health and epidemic-response decisions.

Disease modeling expertise is scarce, especially in the low- and middle-income
countries where outbreaks hit hardest. If AI agents can reliably build correct,
idiomatic Starsim models, they can lower the barrier to rigorous epidemiological
analysis. This benchmark measures whether they can — scoring agents not just on
whether their code runs, but on whether it genuinely *uses Starsim as a library*
rather than reinventing it. We evaluate Claude (Sonnet and Opus), with and
without the [Starsim AI plugin](https://github.com/starsimhub/starsim_ai), across
a graded set of modeling problems.

## What's here

- An **evaluation benchmark** ([inspect-ai](https://inspect.ai-safety-institute.org.uk/))
  with one-shot (prompt) and iterative (agent) modes.
- A **Claude Code A2A server** that exposes Claude Code as a callable coding
  agent over HTTP.
- A **Streamlit problem browser** for exploring the dataset.

## Documentation

| Page | What it covers |
|------|----------------|
| [Getting started](getting-started.md) | Step-by-step: install, start a server, run your first problem. |
| [Evaluation dataset](evaluation.md) | What the benchmark measures, problem structure, scoring, and modes. |
| [Architecture](architecture.md) | How the A2A server and executor are built. |
| [Execution logging](execution-logging.md) | Structured JSONL logs and how to read them. |
| [API reference](reference/claude_a2a.md) | Auto-generated reference for the `claude_a2a` and `eval` packages. |

New here? Start with [Getting started](getting-started.md).

## Quick start

For those who already know the system:

1. Install packages and set up `.env` (`uv sync`; add `ANTHROPIC_API_KEY`).
2. `./docker_up.sh` — start the Claude A2A servers that run the evaluation.
3. `./run_eval.sh` — run the evaluation across models and configurations.

The full README in the repository root has detailed setup, Docker, and CLI
reference tables.
