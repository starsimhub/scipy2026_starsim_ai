# Starsim Evaluation using `inspect_ai`

## Quick start

1. Install dependencies (`pip install -e .` or `uv sync`)
2. Run `run.sh` to run all evaluations.

## Setup

Install dependencies:

```bash
uv sync
```

## Evaluation Modes

### Prompt Evaluation (one-shot)

Tests a model's ability to generate Starsim code in a single attempt. The model receives a problem description and function signature, and must return a complete implementation.

```bash
inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 --temperature 0
```

Model shorthands (used in `run.sh`):

| Shorthand | `--model` value |
|-----------|-----------------|
| `sonnet` | `anthropic/claude-sonnet-4-6` |
| `opus` | `anthropic/claude-opus-4-6` |
| `gpt-5-mini` | `openai/gpt-5-mini-2025-08-07` |
| `gpt-5.2` | `openai/gpt-5.2-2025-12-11` |

#### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--model <model_id>` | Full model ID (see table above) | — |
| `--temperature <float>` | Sampling temperature | model default |
| `-T problems_dir=<path>` | Path to problems JSONL directory | `./problems` |
| `-T tutorial=<id>` | Run only a specific tutorial (e.g., `starsim_t1`) | all |
| `-T with_background=True/False` | Include background context in prompts | `True` |
| `-T timeout=<seconds>` | Timeout per test case execution | `60` |
| `--limit <n>` | Limit number of samples to evaluate | all |

#### Examples

Run a single tutorial:

```bash
inspect eval eval/prompt/starsim.py \
    --model anthropic/claude-sonnet-4-6 \
    --temperature 0 \
    -T tutorial=starsim_t1
```

Run without background context:

```bash
inspect eval eval/prompt/starsim.py \
    --model anthropic/claude-sonnet-4-6 \
    --temperature 0 \
    -T with_background=False
```

### Agent Evaluation

Tests an agent's ability to iteratively write and debug Starsim code. Problems are sent to a Claude Code A2A server, which can write code, run tests, observe errors, and refine its solution.

The agent receives the problem description, function signature, **and test cases** — so it can self-test and iterate before submitting a final answer.

#### Prerequisites

Start the Claude Code A2A server:

```bash
python -m claude_a2a.claude_code_server --port 9100
```

#### Usage

```bash
inspect eval eval/agent/starsim.py -T model=sonnet
```

#### Options

| Flag | Description | Default |
|------|-------------|---------|
| `-T model=<model>` | Agent model: `sonnet` or `opus` | `sonnet` |
| `-T with_plugin=True/False` | Use plugin-enabled server variant | `False` |
| `-T problems_dir=<path>` | Path to problems JSONL directory | `./problems` |
| `-T tutorial=<id>` | Run only a specific tutorial (e.g., `starsim_t1`) | all |
| `-T with_background=True/False` | Include background context in prompts | `True` |
| `-T timeout=<seconds>` | Timeout per test case execution | `60` |
| `-T request_timeout=<seconds>` | HTTP timeout for agent requests | `600` |
| `--limit <n>` | Limit number of samples to evaluate | all |

#### Examples

Run a single tutorial against the agent:

```bash
inspect eval eval/agent/starsim.py \
    -T model=sonnet \
    -T tutorial=starsim_t1
```

## Metrics

Both evaluations share the same metrics:

- **mean**: Average score across sub-steps (1.0 if all tests pass, 0.0 otherwise)
- **sub_step_accuracy**: Fraction of sub-steps where all tests pass
- **test_pass_rate**: Fraction of individual test cases that pass across all sub-steps
