"""Starsim evaluation benchmark using inspect_ai.

Evaluates LLM ability to write Starsim simulation code by presenting
function specifications and scoring generated code against test cases.

Usage:
    inspect eval eval/llm/starsim.py --model <your_model> --temperature 0

Options:
    -T problems_dir=<path>       Path to problems JSONL directory (default: ./problems)
    -T tutorial=<id>             Run only a specific tutorial, e.g. "starsim_t1"
    -T with_background=True      Include background context in prompts (default: True)
    -T with_test_cases=False     Include test cases in prompts (default: False)
    -T timeout=60                Timeout in seconds for test execution (default: 60)
"""

from dotenv import load_dotenv
load_dotenv()

import sys
import textwrap
from pathlib import Path

# Ensure the project root is on sys.path so `eval.shared` can be imported
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset
from inspect_ai.scorer import (
    Score,
    Target,
    mean,
    scorer,
)
from inspect_ai.solver import Generate, TaskState, solver

from eval.shared import (
    extract_python_code,
    load_problems,
    run_tests,
    sub_step_accuracy,
    test_pass_rate,
)


PROMPT_TEMPLATE = textwrap.dedent("""\
    Write a Python function that solves the following problem.

    ## Dependencies
    {dependencies}

    ## Problem Description
    {description}

    {background_section}

    ## Function Signature
    ```python
    {function_header}
        \"\"\"{docstring}\"\"\"
    ```

    {test_cases_section}

    Return ONLY the function implementation inside a single ```python``` code block.
    Include any necessary import statements inside the function body.
""")


def _format_test_cases(test_cases: list[dict]) -> str:
    """Format test cases for inclusion in the prompt."""
    parts = []
    for tc in test_cases:
        parts.append(f"### {tc['description']}\n```python\n{tc['test']}\n```")
    return "\n\n".join(parts)


@solver
def starsim_solver(with_background: bool = True, with_test_cases: bool = False):
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata
        deps = ", ".join(meta["dependencies"])
        background_section = (
            f"## Background\n{meta['background']}" if with_background else ""
        )
        test_cases_section = (
            "## Test Cases\nThe following test cases will be used to verify your solution:\n\n"
            + _format_test_cases(meta["test_cases"])
            if with_test_cases
            else ""
        )
        prompt = PROMPT_TEMPLATE.format(
            dependencies=deps,
            description=meta["description"],
            background_section=background_section,
            function_header=meta["function_header"],
            docstring=meta["docstring"],
            test_cases_section=test_cases_section,
        )
        state.user_prompt.text = prompt
        return await generate(state)

    return solve


@scorer(metrics=[mean(), sub_step_accuracy(), test_pass_rate()])
def starsim_scorer(timeout: int = 60):
    async def score(state: TaskState, target: Target) -> Score:
        response = state.output.completion
        code = extract_python_code(response)
        test_cases = state.metadata["test_cases"]

        passed, total, errors = run_tests(
            code, test_cases, state.metadata["dependencies"], timeout
        )
        value = 1.0 if passed == total else 0.0

        return Score(
            value=value,
            explanation="\n".join(errors) if errors else "All tests passed",
            metadata={
                "tests_passed": passed,
                "tests_total": total,
                "sub_step_id": state.metadata["sub_step_id"],
                "problem_id": state.metadata["problem_id"],
            },
        )

    return score


@task
def starsim_benchmark(
    problems_dir: str = str(Path(__file__).resolve().parent.parent.parent / "problems"),
    tutorial: str | None = None,
    with_background: bool = True,
    with_test_cases: bool = False,
    timeout: int = 60,
) -> Task:
    """Starsim coding evaluation benchmark.

    Args:
        problems_dir: Path to directory containing problem JSONL files.
        tutorial: Optional tutorial ID to filter (e.g. "starsim_t1").
        with_background: Whether to include background context in prompts.
        with_test_cases: Whether to include test cases in prompts.
        timeout: Timeout in seconds for each test case execution.
    """
    samples = load_problems(problems_dir, tutorial)
    dataset = MemoryDataset(samples=samples, name="starsim")

    return Task(
        dataset=dataset,
        solver=starsim_solver(with_background=with_background, with_test_cases=with_test_cases),
        scorer=starsim_scorer(timeout=timeout),
    )
