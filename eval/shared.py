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
    """Run test cases against generated code. Returns (passed, total, errors)."""
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
