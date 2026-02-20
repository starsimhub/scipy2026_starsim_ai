"""
Validate that all problem JSONL files are well-formed and that gold solutions
pass their test cases.

Usage:
    uv run pytest tests/test_problems.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROBLEMS_DIR = Path(__file__).resolve().parent.parent / "problems"


def load_substeps() -> list[dict]:
    """Load all sub-steps from every JSONL file in the problems directory."""
    substeps = []
    for path in sorted(PROBLEMS_DIR.glob("*.jsonl")):
        with open(path) as f:
            for line_num, line in enumerate(f, 1):
                step = json.loads(line)
                step["_source"] = f"{path.name}:{line_num}"
                substeps.append(step)
    return substeps


REQUIRED_FIELDS = [
    "problem_id",
    "sub_step_id",
    "description",
    "function_header",
    "docstring",
    "dependencies",
    "test_cases",
    "gold_solution",
]

ALL_SUBSTEPS = load_substeps()


@pytest.mark.parametrize(
    "substep",
    ALL_SUBSTEPS,
    ids=[s["sub_step_id"] for s in ALL_SUBSTEPS],
)
def test_schema(substep):
    """Each sub-step has all required fields."""
    for field in REQUIRED_FIELDS:
        assert field in substep, f"{substep['_source']}: missing field '{field}'"


@pytest.mark.parametrize(
    "substep",
    ALL_SUBSTEPS,
    ids=[s["sub_step_id"] for s in ALL_SUBSTEPS],
)
def test_gold_solution(substep):
    """Gold solution passes all test cases for the sub-step."""
    # Build a namespace with the gold solution defined
    ns: dict = {}
    exec(substep["gold_solution"], ns)

    for tc in substep["test_cases"]:
        # Each test case can reference the function defined in the gold solution
        try:
            exec(tc["test"], ns)
        except AssertionError:
            raise
        except Exception as exc:
            pytest.fail(
                f"{substep['sub_step_id']} / {tc['description']}: {type(exc).__name__}: {exc}"
            )
