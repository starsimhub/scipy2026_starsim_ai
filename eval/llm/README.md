# Starsim Evaluation using `inspect_ai`

## Setup

Install dependencies:

```bash
uv sync
```

## Usage

Run the full benchmark:

```bash
inspect eval eval/llm/starsim.py --model <your_model> --temperature 0
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `-T problems_dir=<path>` | Path to problems JSONL directory | `./problems` |
| `-T tutorial=<id>` | Run only a specific tutorial (e.g., `starsim_t1`) | all |
| `-T with_background=True/False` | Include background context in prompts | `True` |
| `-T timeout=<seconds>` | Timeout per test case execution | `60` |
| `--limit <n>` | Limit number of samples to evaluate | all |

### Examples

Run a single tutorial:

```bash
inspect eval eval/llm/starsim.py \
    --model openai/gpt-4o \
    --temperature 0 \
    -T tutorial=starsim_t1
```

Run without background context:

```bash
inspect eval eval/llm/starsim.py \
    --model anthropic/claude-sonnet-4-20250514 \
    --temperature 0 \
    -T with_background=False
```

## Metrics

- **mean**: Average score across sub-steps (1.0 if all tests pass, 0.0 otherwise)
- **sub_step_accuracy**: Fraction of sub-steps where all tests pass
- **test_pass_rate**: Fraction of individual test cases that pass across all sub-steps
