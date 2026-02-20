"""Starsim agent evaluation benchmark using inspect_ai.

Evaluates an agent's ability to write Starsim simulation code by sending
problems to a Claude Code A2A server and scoring the generated code
against test cases.

The agent can iteratively write, test, and refine code — unlike the LLM
eval which only gets a single generation attempt.

Prerequisites:
    Start the Claude Code A2A server before running:
        python -m ssai.claude_code_server --port 9100

Usage:
    inspect eval eval/agent/starsim.py -T agent_url=http://localhost:9100

Options:
    -T agent_url=<url>           A2A server URL (default: http://localhost:9100)
    -T problems_dir=<path>       Path to problems JSONL directory (default: ./problems)
    -T tutorial=<id>             Run only a specific tutorial, e.g. "starsim_t1"
    -T with_background=True      Include background context in prompts (default: True)
    -T timeout=60                Timeout in seconds for test execution (default: 60)
    -T request_timeout=300       HTTP timeout for agent requests (default: 300)
"""

from dotenv import load_dotenv
load_dotenv()

import logging
import sys
import textwrap
from pathlib import Path
from uuid import uuid4

# Ensure the project root is on sys.path so `eval.shared` can be imported
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import httpx

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset
from inspect_ai.model import ChatMessageAssistant, ModelOutput
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

logger = logging.getLogger(__name__)


AGENT_PROMPT_TEMPLATE = textwrap.dedent("""\
    Write a Python function that solves the following problem.
    You have access to a workspace where you can write and test code.

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

    ## Test Cases
    The following test cases will be used to verify your solution.
    You can use these to test your implementation:

    {test_cases_section}

    ## Instructions
    1. Write the function implementation
    2. Test it against the provided test cases
    3. Fix any issues and re-test until all tests pass
    4. Return your final function implementation in a ```python``` code block
""")


def _format_test_cases(test_cases: list[dict]) -> str:
    """Format test cases for inclusion in the agent prompt."""
    parts = []
    for tc in test_cases:
        parts.append(f"### {tc['description']}\n```python\n{tc['test']}\n```")
    return "\n\n".join(parts)


def _make_a2a_request(text: str) -> dict:
    """Build a JSON-RPC 2.0 message/send request for the A2A server."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
                "messageId": str(uuid4()),
            },
        },
    }


def _extract_a2a_response(data: dict) -> str:
    """Extract text content from an A2A JSON-RPC response."""
    if "error" in data:
        error = data["error"]
        raise RuntimeError(f"A2A server error: {error}")

    result = data.get("result", {})

    # Check for artifacts (where the final response lives)
    artifacts = result.get("artifacts", [])
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                return part["text"]

    # Fallback: check status message
    status = result.get("status", {})
    message = status.get("message", {})
    for part in message.get("parts", []):
        if part.get("kind") == "text":
            return part["text"]

    return ""


@solver
def a2a_agent_solver(
    agent_url: str = "http://localhost:9100",
    with_background: bool = True,
    request_timeout: int = 300,
):
    """Solver that sends problems to a Claude Code A2A server."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata
        deps = ", ".join(meta["dependencies"])
        background_section = (
            f"## Background\n{meta['background']}" if with_background else ""
        )
        test_cases_section = _format_test_cases(meta["test_cases"])

        prompt = AGENT_PROMPT_TEMPLATE.format(
            dependencies=deps,
            description=meta["description"],
            background_section=background_section,
            function_header=meta["function_header"],
            docstring=meta["docstring"],
            test_cases_section=test_cases_section,
        )

        logger.info(
            "Sending problem %s to A2A server at %s",
            meta["sub_step_id"],
            agent_url,
        )

        payload = _make_a2a_request(prompt)

        async with httpx.AsyncClient(timeout=request_timeout) as client:
            resp = await client.post(agent_url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        response_text = _extract_a2a_response(data)

        logger.info(
            "Received response for %s (length=%d)",
            meta["sub_step_id"],
            len(response_text),
        )

        # Set the output so the scorer can evaluate it
        state.output = ModelOutput.from_content(
            model="a2a-agent",
            content=response_text,
        )
        state.messages.append(ChatMessageAssistant(content=response_text))

        return state

    return solve


@scorer(metrics=[mean(), sub_step_accuracy(), test_pass_rate()])
def agent_scorer(timeout: int = 60):
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
def starsim_agent_benchmark(
    agent_url: str = "http://localhost:9100",
    problems_dir: str = str(Path(__file__).resolve().parent.parent.parent / "problems"),
    tutorial: str | None = None,
    with_background: bool = True,
    timeout: int = 60,
    request_timeout: int = 300,
) -> Task:
    """Starsim agent coding evaluation benchmark.

    Sends problems to a Claude Code A2A server and evaluates the
    generated code against test cases.

    Args:
        agent_url: URL of the A2A server.
        problems_dir: Path to directory containing problem JSONL files.
        tutorial: Optional tutorial ID to filter (e.g. "starsim_t1").
        with_background: Whether to include background context in prompts.
        timeout: Timeout in seconds for each test case execution.
        request_timeout: HTTP timeout in seconds for agent requests.
    """
    samples = load_problems(problems_dir, tutorial)
    dataset = MemoryDataset(samples=samples, name="starsim_agent")

    return Task(
        dataset=dataset,
        solver=a2a_agent_solver(
            agent_url=agent_url,
            with_background=with_background,
            request_timeout=request_timeout,
        ),
        scorer=agent_scorer(timeout=timeout),
    )
