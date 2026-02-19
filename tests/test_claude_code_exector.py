"""
Test client that exercises the Claude Code A2A server.

Demonstrates:
  1. Agent Card discovery
  2. Simple one-shot message/send
  3. Streaming message/sendStream
  4. Multi-turn conversation (resume a task)

Usage:
    # Start the server first:
    python -m sandbagging_workshop.claude_code_server --port 9100

    # Then run the tests:
    pytest tests/test_claude_code_exector.py -v -s
"""

from __future__ import annotations

import json
import subprocess
import sys
import time

import httpx
import pytest
from httpx_sse import connect_sse

pytestmark = pytest.mark.uses_llm

JSONRPC_VERSION = "2.0"
PORT = 9100
BASE_URL = f"http://localhost:{PORT}"
STARTUP_TIMEOUT = 15  # seconds to wait for the server to be ready
REQUEST_TIMEOUT = 120  # seconds to wait for a response


@pytest.fixture(scope="module")
def claude_code_server():
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m", "ssai.claude_code_server",
            "--port", str(PORT),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Wait until the server accepts connections
    deadline = time.time() + STARTUP_TIMEOUT
    ready = False
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{BASE_URL}/.well-known/agent.json", timeout=2)
            if resp.status_code == 200:
                ready = True
                break
        except httpx.ConnectError:
            time.sleep(0.5)

    if not ready:
        proc.terminate()
        proc.wait()
        pytest.fail("Claude Code A2A server did not start in time")

    yield proc

    proc.terminate()
    proc.wait()


def make_request(method: str, params: dict, req_id: int = 1) -> dict:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": req_id,
        "method": method,
        "params": params,
    }


def make_message(text: str, task_id: str | None = None, context_id: str | None = None) -> dict:
    params: dict = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": text}],
            "messageId": f"msg-{id(text)}",
        },
    }
    if task_id:
        params["taskId"] = task_id
    if context_id:
        params["contextId"] = context_id
    return params


# ---------------------------------------------------------------------------
# 1. Discover the Agent Card
# ---------------------------------------------------------------------------

def test_discover_agent(claude_code_server):
    with httpx.Client() as client:
        resp = client.get(f"{BASE_URL}/.well-known/agent.json")
        resp.raise_for_status()
        card = resp.json()

    assert "name" in card
    assert "version" in card


# ---------------------------------------------------------------------------
# 2. One-shot message/send
# ---------------------------------------------------------------------------

def test_send(claude_code_server):
    payload = make_request(
        "message/send",
        make_message("Write a Python function that checks if a number is prime. Keep it short."),
    )

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        resp = client.post(BASE_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()

    assert "error" not in data, f"JSON-RPC error: {data.get('error')}"

    result = data.get("result", {})
    assert "status" in result or "parts" in result


# ---------------------------------------------------------------------------
# 3. Streaming message/sendStream
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="not working")
def test_stream(claude_code_server):
    payload = make_request(
        "message/sendStream",
        make_message("List 3 creative project ideas for a weekend hackathon. Be brief."),
    )

    events = []
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        with connect_sse(client, "POST", BASE_URL, json=payload) as event_source:
            event_source.response.raise_for_status()
            for sse in event_source.iter_sse():
                try:
                    event = json.loads(sse.data)
                    events.append(event)
                except json.JSONDecodeError:
                    pass

    assert len(events) > 0, "Expected at least one SSE event"


# ---------------------------------------------------------------------------
# 4. Multi-turn conversation
# ---------------------------------------------------------------------------

def test_multi_turn(claude_code_server):
    # Turn 1: Initial request
    payload1 = make_request(
        "message/send",
        make_message("Write a Python function called `greet` that takes a name and returns a greeting string."),
        req_id=1,
    )

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        resp1 = client.post(BASE_URL, json=payload1)
        data1 = resp1.json()

    result1 = data1.get("result", {})
    task_id = result1.get("id")
    context_id = result1.get("contextId")

    assert task_id is not None, "No task ID returned from turn 1"

    # Turn 2: Follow up on the same task
    payload2 = make_request(
        "message/send",
        make_message(
            "Now write a unit test for the `greet` function you just created.",
            task_id=task_id,
            context_id=context_id,
        ),
        req_id=2,
    )

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        resp2 = client.post(BASE_URL, json=payload2)
        data2 = resp2.json()

    assert "error" not in data2, f"JSON-RPC error on turn 2: {data2.get('error')}"
