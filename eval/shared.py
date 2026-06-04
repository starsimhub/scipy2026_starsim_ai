"""Shared utilities for Starsim evaluation benchmarks.

Used by both the LLM (one-shot) and agent-based evaluations.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from inspect_ai.dataset import Sample
from inspect_ai.scorer import (
    Metric,
    SampleScore,
    metric,
)


def extract_python_code(response: str) -> str:
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


def load_problems(problems_dir: str, tutorial: str | None = None) -> list[Sample]:
    """Load problem JSONL files and convert them to inspect_ai Samples.

    Reads every ``starsim_t*.jsonl`` file in *problems_dir* and turns each
    sub-step record into an inspect_ai ``Sample`` whose ``metadata`` holds the
    full problem definition (description, function header, test cases, etc.).

    Args:
        problems_dir: Directory containing the generated ``starsim_t*.jsonl`` files.
        tutorial: Optional problem ID (e.g. ``"starsim_t1"``) to load a single
            tutorial. When ``None``, all tutorials are loaded.

    Returns:
        A list of samples ready to wrap in a ``MemoryDataset``.

    Example:
        ```python
        from inspect_ai.dataset import MemoryDataset
        from eval.shared import load_problems

        samples = load_problems("./problems", tutorial="starsim_t1")
        dataset = MemoryDataset(samples=samples, name="starsim")
        ```

    See Also:
        [`run_tests`][eval.shared.run_tests]: scores a solution against a
        sample's ``test_cases`` metadata.
    """
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


_DEPENDENCY_IMPORTS = {
    "starsim": "import starsim as ss",
    "numpy": "import numpy as np",
}


def make_preamble(dependencies: list[str]) -> str:
    """Generate import statements for the given dependencies."""
    lines = [_DEPENDENCY_IMPORTS[dep] for dep in dependencies if dep in _DEPENDENCY_IMPORTS]
    return "\n".join(lines)


def run_tests(
    code: str,
    test_cases: list[dict],
    dependencies: list[str],
    timeout: int,
) -> tuple[int, int, list[str]]:
    """Run test cases against generated code.

    Each test case is concatenated with a dependency import preamble and the
    candidate *code*, then executed in its own subprocess. A case passes if the
    subprocess exits cleanly within *timeout* seconds.

    Args:
        code: The candidate solution (typically a single function definition).
        test_cases: Test-case dicts, each with ``"test"`` (code) and
            ``"description"`` keys.
        dependencies: Package names (e.g. ``["starsim", "numpy"]``) used to
            build the import preamble prepended to every test.
        timeout: Per-test-case wall-clock limit, in seconds.

    Returns:
        A ``(passed, total, errors)`` tuple: the number of cases that passed,
        the total number of cases, and a list of failure/timeout messages.

    Example:
        ```python
        from eval.shared import load_problems, run_tests

        problem = load_problems("./problems", tutorial="starsim_t1")[0].metadata
        passed, total, errors = run_tests(
            code=problem["gold_solution"],
            test_cases=problem["test_cases"],
            dependencies=problem["dependencies"],
            timeout=60,
        )
        assert passed == total, errors
        ```

    See Also:
        [`load_problems`][eval.shared.load_problems]: supplies the test cases
        and dependencies for a problem.
    """
    preamble = make_preamble(dependencies)
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


def format_test_cases(test_cases: list[dict]) -> str:
    """Format test cases for inclusion in a prompt."""
    parts = []
    for tc in test_cases:
        parts.append(f"### {tc['description']}\n```python\n{tc['test']}\n```")
    return "\n\n".join(parts)


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
