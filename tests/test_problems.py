"""
Validate that all problem JSONL files are well-formed and that gold solutions
pass their test cases.

Usage:
    uv run pytest tests/test_problems.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
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


def test_jsonl_matches_markdown():
    """JSONL files are up-to-date with their markdown sources."""
    md_files = sorted(PROBLEMS_DIR.glob("starsim_t*.md"))
    assert md_files, "No markdown files found in problems/"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run build_jsonl.py but write output to a temp dir so we don't
        # overwrite the checked-in files.
        build_script = PROBLEMS_DIR / "build_jsonl.py"
        assert build_script.exists(), "problems/build_jsonl.py not found"

        # Import the build module and generate JSONL to a temp location
        tmpdir = Path(tmpdir)
        for md_path in md_files:
            # Import parse_markdown from build_jsonl
            sys.path.insert(0, str(PROBLEMS_DIR))
            try:
                from build_jsonl import parse_markdown
            finally:
                sys.path.pop(0)

            text = md_path.read_text()
            problems = parse_markdown(text)
            tmp_jsonl = tmpdir / md_path.with_suffix(".jsonl").name
            with open(tmp_jsonl, "w") as f:
                for problem in problems:
                    f.write(json.dumps(problem) + "\n")

            # Compare with the checked-in JSONL
            checked_in = md_path.with_suffix(".jsonl")
            assert checked_in.exists(), f"{checked_in.name} not found"

            expected = []
            with open(checked_in) as f:
                for line in f:
                    if line.strip():
                        expected.append(json.loads(line))

            assert len(problems) == len(expected), (
                f"{checked_in.name}: markdown has {len(problems)} problems "
                f"but JSONL has {len(expected)}"
            )
            for i, (got, want) in enumerate(zip(problems, expected)):
                assert got == want, (
                    f"{checked_in.name} line {i + 1} ({got.get('sub_step_id', '?')}): "
                    f"JSONL does not match markdown. "
                    f"Run 'python3 problems/build_jsonl.py' to regenerate."
                )


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
