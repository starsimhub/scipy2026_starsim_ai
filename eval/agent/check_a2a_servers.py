#!/usr/bin/env python
"""Confirm that all four Docker A2A servers are responding correctly.

Checks that the Starsim-AI plugin is available to plugin servers and absent
from non-plugin servers, for both Sonnet and Opus models.

Queries all servers in parallel.

Usage:
    python eval/agent/check_a2a_servers.py
    python eval/agent/check_a2a_servers.py --timeout 180
"""

import argparse
import sciris as sc
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed


QUESTION = """
What version of the Starsim AI plugin are you using, if any? Start your answer with YES or NO with no formatting.
Explain your answer briefly.
If YES, also give the plugin version number (which this plugin provides in the starsim-dev skill).
Then list the skills and MCP servers available.
Also report which LLM model you are using.
"""

# (label, default_url, expects_plugin, expected_model)
SERVERS = [
    ("sonnet",        "http://localhost:9100", False, "sonnet"),
    ("sonnet-plugin", "http://localhost:9101", True,  "sonnet"),
    ("opus",          "http://localhost:9102", False, "opus"),
    ("opus-plugin",   "http://localhost:9103", True,  "opus"),
]


def query_server(url: str, timeout: int = 120) -> str:
    """Send the plugin question to an A2A server and return the response text."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": QUESTION}],
                "messageId": str(sc.uuid()),
            },
        },
    }
    resp = httpx.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"A2A error: {data['error']}")

    # Check artifacts first, then status message
    for artifact in data.get("result", {}).get("artifacts", []):
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                return part["text"]

    status = data.get("result", {}).get("status", {})
    for part in status.get("message", {}).get("parts", []):
        if part.get("kind") == "text":
            return part["text"]

    return ""


def check_server(label: str, url: str, expects_plugin: bool, expected_model: str, timeout: int) -> tuple[str, bool, str]:
    """Query a server and check the response. Returns (label, passed, message)."""
    try:
        response = query_server(url, timeout=timeout)
    except Exception as e:
        return label, False, f"ERROR: {e}"

    verdicts = []
    all_passed = True

    # Check plugin status
    first_line = response.strip().split()[0] if response.strip() else ""
    has_yes = "YES" in first_line
    has_no = "NO" in first_line
    if not (has_yes or has_no) or (has_yes and has_no):
        verdicts.append(f"FAIL: response does not start with YES or NO as expected")
        all_passed = False
    elif expects_plugin:
        if has_yes:
            verdicts.append("PASS: server reports having the plugin")
        else:
            verdicts.append("FAIL: expected plugin but response doesn't start with YES")
            all_passed = False
    else:
        if has_no:
            verdicts.append("PASS: server reports no plugin")
        else:
            verdicts.append("FAIL: expected no plugin but response doesn't start with NO")
            all_passed = False

    # Check model
    response_lower = response.lower()
    if expected_model in response_lower:
        verdicts.append(f"PASS: server reports {expected_model} model")
    else:
        verdicts.append(f"FAIL: expected {expected_model} model but not found in response")
        all_passed = False

    detail = f"Response: {response}\n  " + "\n  ".join(verdicts)
    return label, all_passed, detail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=120)
    for label, default_url, *_ in SERVERS:
        parser.add_argument(f"--{label}-url", default=default_url)
    args = parser.parse_args()

    # Build server list with possibly overridden URLs
    servers = []
    for label, default_url, expects_plugin, expected_model in SERVERS:
        url = getattr(args, label.replace("-", "_") + "_url")
        servers.append((label, url, expects_plugin, expected_model))

    # Query all servers in parallel
    print('Starting check of:\n', servers)
    results = {}
    with ThreadPoolExecutor(max_workers=len(servers)) as pool:
        futures = {
            pool.submit(check_server, label, url, expects_plugin, expected_model, args.timeout): label
            for label, url, expects_plugin, expected_model in servers
        }
        for future in as_completed(futures):
            label, passed, detail = future.result()
            results[label] = (passed, detail)

    # Print results in deterministic order
    ok = True
    for label, url, *_ in servers:
        passed, detail = results[label]
        print(f"\n{'='*60}")
        print(f"{label} ({url})")
        print(f"  {detail}")
        if passed:
            sc.printgreen(f"  >> {label}: PASS")
        else:
            sc.printred(f"  >> {label}: FAIL")
            ok = False

    print(f"\n{'='*60}")
    if ok:
        sc.printgreen("All checks passed.")
    else:
        sc.printred("Some checks FAILED.")
    return


if __name__ == "__main__":
    with sc.timer():
        main()
