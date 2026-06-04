# API reference: `eval`

The `eval` package holds the [inspect-ai](https://inspect.ai-safety-institute.org.uk/)
evaluation harness. See [Evaluation dataset](../evaluation.md) for what these
benchmarks measure.

## Shared utilities

::: eval.shared
    options:
      members:
        - load_problems
        - run_tests
        - extract_python_code
        - make_preamble
        - format_test_cases
        - sub_step_accuracy
        - test_pass_rate

## Prompt benchmark (one-shot)

::: eval.prompt.starsim
    options:
      members:
        - starsim_benchmark

## Agent benchmark (iterative)

::: eval.agent.starsim
    options:
      members:
        - starsim_agent_benchmark
