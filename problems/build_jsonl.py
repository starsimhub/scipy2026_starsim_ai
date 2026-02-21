#!/usr/bin/env python3
"""Convert markdown problem files to JSONL format.

Usage:
    python problems/build_jsonl.py              # convert all .md files in problems/
    python problems/build_jsonl.py starsim_t1   # convert a single tutorial
"""

import json
import re
import sys
from pathlib import Path

PROBLEMS_DIR = Path(__file__).parent


def parse_markdown(text: str) -> list[dict]:
    """Parse a tutorial markdown file into a list of problem dicts."""
    problems = []
    # Split into sub-step sections (## headings)
    sub_step_chunks = re.split(r"^## ", text, flags=re.MULTILINE)

    # First chunk is the file-level header (# heading); skip it
    for chunk in sub_step_chunks[1:]:
        problem = _parse_sub_step(chunk)
        problems.append(problem)

    return problems


def _parse_sub_step(chunk: str) -> dict:
    """Parse a single sub-step chunk (text after '## ')."""
    lines = chunk.split("\n")
    sub_step_id = lines[0].strip()
    problem_id = sub_step_id.rsplit(".", 1)[0]

    # Extract sections by ### headings
    sections = _extract_sections(chunk)

    # Parse test cases
    test_cases = _parse_test_cases(sections.get("Test Cases", ""))

    return {
        "problem_id": problem_id,
        "sub_step_id": sub_step_id,
        "description": sections.get("Description", "").strip(),
        "function_header": _extract_code_block(sections.get("Function Header", "")),
        "docstring": _extract_raw_block(sections.get("Docstring", "")),
        "background": sections.get("Background", "").strip(),
        "dependencies": _parse_dependencies(sections.get("Dependencies", "")),
        "test_cases": test_cases,
        "gold_solution": _extract_code_block(sections.get("Gold Solution", "")),
    }


def _extract_sections(chunk: str) -> dict[str, str]:
    """Split a sub-step chunk into named sections by ### headings."""
    sections = {}
    parts = re.split(r"^### (.+)$", chunk, flags=re.MULTILINE)
    # parts[0] is text before first ###, parts[1] is heading, parts[2] is body, etc.
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        sections[heading] = body
    return sections


def _extract_code_block(text: str) -> str:
    """Extract the content of the first fenced code block."""
    match = re.search(r"```\w*\n(.*?)```", text, re.DOTALL)
    return match.group(1).rstrip("\n") if match else text.strip()


def _extract_raw_block(text: str) -> str:
    """Extract the content of a fenced code block, preserving internal whitespace."""
    match = re.search(r"```\w*\n(.*?)```", text, re.DOTALL)
    return match.group(1).rstrip("\n") if match else text.strip()


def _parse_dependencies(text: str) -> list[str]:
    """Parse a markdown list of dependencies."""
    deps = re.findall(r"^- (.+)$", text.strip(), re.MULTILINE)
    return [d.strip() for d in deps] if deps else []


def _parse_test_cases(text: str) -> list[dict]:
    """Parse test cases from #### headings with code blocks."""
    test_cases = []
    parts = re.split(r"^#### (.+)$", text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        description = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        code = _extract_code_block(body)
        test_cases.append({"description": description, "test": code})
    return test_cases


def convert_file(md_path: Path) -> Path:
    """Convert a single markdown file to JSONL."""
    text = md_path.read_text()
    problems = parse_markdown(text)

    jsonl_path = md_path.with_suffix(".jsonl")
    with open(jsonl_path, "w") as f:
        for problem in problems:
            f.write(json.dumps(problem) + "\n")

    print(f"  {md_path.name} -> {jsonl_path.name} ({len(problems)} problems)")
    return jsonl_path


def main():
    if len(sys.argv) > 1:
        names = sys.argv[1:]
    else:
        names = sorted(
            p.stem for p in PROBLEMS_DIR.glob("*.md") if p.stem != "README"
        )

    if not names:
        print("No markdown files found in", PROBLEMS_DIR)
        sys.exit(1)

    print(f"Building JSONL from {len(names)} markdown file(s):")
    for name in names:
        md_path = PROBLEMS_DIR / f"{name}.md"
        if not md_path.exists():
            print(f"  WARNING: {md_path} not found, skipping")
            continue
        convert_file(md_path)

    print("Done.")


if __name__ == "__main__":
    main()
