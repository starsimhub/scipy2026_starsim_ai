"""Starsim evaluation benchmark using inspect_ai.

Evaluates LLM ability to write Starsim simulation code by presenting
function specifications and scoring generated code against test cases.

Usage:
    inspect eval eval/llm/starsim.py --model <your_model> --temperature 0

Options:
    -T problems_dir=<path>       Path to problems JSONL directory (default: ./problems)
    -T tutorial=<id>             Run only a specific tutorial, e.g. "starsim_t1"
    -T with_background=True      Include background context in prompts (default: True)
    -T timeout=60                Timeout in seconds for test execution (default: 60)
"""

from dotenv import load_dotenv
load_dotenv()

import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, MemoryDataset
from inspect_ai.scorer import (
    SampleScore,
    Score,
    Target,
    mean,
    metric,
    Metric,
    scorer,
)
from inspect_ai.solver import Generate, TaskState, solver


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

    Return ONLY the function implementation inside a single ```python``` code block.
    Include any necessary import statements inside the function body.
""")


def _extract_python_code(response: str) -> str:
    """Extract Python code from a markdown code block."""
    # Find the last ```python ... ``` block
    parts = response.split("```python")
    if len(parts) < 2:
        # Try without language specifier
        parts = response.split("```")
        if len(parts) < 3:
            return response
        code = parts[-2]
    else:
        code = parts[-1]
    # Remove trailing ```
    code = code.split("```")[0]
    return code.strip()


def _load_problems(problems_dir: str, tutorial: str | None = None) -> list[Sample]:
    """Load problem JSONL files and convert to inspect_ai Samples."""
    problems_path = Path(problems_dir)
    samples = []
    for jsonl_file in sorted(problems_path.glob("starsim_t*.jsonl")):
        with open(jsonl_file) as f:
            for line in f:
                record = json.loads(line)
                if tutorial and record["problem_id"] != tutorial:
                    continue
                samples.append(
                    Sample(
                        input="placeholder",
                        target=record["sub_step_id"],
                        id=record["sub_step_id"],
                        metadata=record,
                    )
                )
    return samples


@solver
def starsim_solver(with_background: bool = True):
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata
        deps = ", ".join(meta["dependencies"])
        background_section = (
            f"## Background\n{meta['background']}" if with_background else ""
        )
        prompt = PROMPT_TEMPLATE.format(
            dependencies=deps,
            description=meta["description"],
            background_section=background_section,
            function_header=meta["function_header"],
            docstring=meta["docstring"],
        )
        state.user_prompt.text = prompt
        return await generate(state)

    return solve


_DEPENDENCY_IMPORTS = {
    "starsim": "import starsim as ss",
    "numpy": "import numpy as np",
}


def _make_preamble(dependencies: list[str]) -> str:
    """Generate import statements for the given dependencies."""
    lines = [_DEPENDENCY_IMPORTS[dep] for dep in dependencies if dep in _DEPENDENCY_IMPORTS]
    return "\n".join(lines)


def _run_tests(
    code: str,
    test_cases: list[dict],
    dependencies: list[str],
    timeout: int,
) -> tuple[int, int, list[str]]:
    """Run test cases against generated code. Returns (passed, total, errors)."""
    preamble = _make_preamble(dependencies)
    passed = 0
    total = len(test_cases)
    errors = []

    for tc in test_cases:
        script = f"{preamble}\n\n{code}\n\n{tc['test']}\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as tmp:
            tmp.write(script)
            tmp.flush()
            try:
                subprocess.run(
                    [sys.executable, tmp.name],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=True,
                )
                passed += 1
            except subprocess.CalledProcessError as e:
                errors.append(
                    f"FAIL [{tc['description']}]: {e.stderr[-500:] if e.stderr else ''}"
                )
            except subprocess.TimeoutExpired:
                errors.append(f"TIMEOUT [{tc['description']}]")
            finally:
                Path(tmp.name).unlink(missing_ok=True)

    return passed, total, errors


@metric
def sub_step_accuracy() -> Metric:
    """Fraction of individual sub-steps where all tests pass."""

    def metric(scores: list[SampleScore]) -> float:
        if not scores:
            return 0.0
        return sum(1 for s in scores if s.score.value == 1.0) / len(scores)

    return metric


@metric
def test_pass_rate() -> Metric:
    """Fraction of individual test cases that pass across all sub-steps."""

    def metric(scores: list[SampleScore]) -> float:
        total_passed = sum(s.score.metadata["tests_passed"] for s in scores)
        total_tests = sum(s.score.metadata["tests_total"] for s in scores)
        return total_passed / total_tests if total_tests > 0 else 0.0

    return metric


@scorer(metrics=[mean(), sub_step_accuracy(), test_pass_rate()])
def starsim_scorer(timeout: int = 60):
    async def score(state: TaskState, target: Target) -> Score:
        response = state.output.completion
        code = _extract_python_code(response)
        test_cases = state.metadata["test_cases"]

        passed, total, errors = _run_tests(
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
def starsim(
    problems_dir: str = str(Path(__file__).resolve().parent.parent.parent / "problems"),
    tutorial: str | None = None,
    with_background: bool = True,
    timeout: int = 60,
) -> Task:
    """Starsim coding evaluation benchmark.

    Args:
        problems_dir: Path to directory containing problem JSONL files.
        tutorial: Optional tutorial ID to filter (e.g. "starsim_t1").
        with_background: Whether to include background context in prompts.
        timeout: Timeout in seconds for each test case execution.
    """
    samples = _load_problems(problems_dir, tutorial)
    dataset = MemoryDataset(samples=samples, name="starsim")

    return Task(
        dataset=dataset,
        solver=starsim_solver(with_background=with_background),
        scorer=starsim_scorer(timeout=timeout),
    )
