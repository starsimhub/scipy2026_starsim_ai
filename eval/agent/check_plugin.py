"""Confirm that the Starsim-AI plugin is available to one Docker server, and not to the other.

Sends a plugin-inquiry prompt to two A2A servers and checks the responses.

Usage:
    python eval/agent/check_plugin.py
    python eval/agent/check_plugin.py --no-plugin-url http://localhost:9100 --plugin-url http://localhost:9101
"""

import sys
import argparse
import httpx
from uuid import uuid4


QUESTION = (
    "What version of the starsim plugin are you using, if any? "
    "Start your answer with YES or NO, then explain briefly."
)


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
                "messageId": str(uuid4()),
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-plugin-url", default="http://localhost:9100")
    parser.add_argument("--plugin-url", default="http://localhost:9101")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    ok = True

    for label, url, expects_plugin in [
        ("no-plugin", args.no_plugin_url, False),
        ("plugin", args.plugin_url, True),
    ]:
        print(f"\n{'='*60}")
        print(f"Querying {label} server at {url} ...")
        try:
            response = query_server(url, timeout=args.timeout)
        except Exception as e:
            print(f"  ERROR: {e}")
            ok = False
            continue

        print(f"  Response: {response[:500]}")

        first_word = response.strip().split()[0].strip(".,!:").upper() if response.strip() else ""
        if expects_plugin:
            if first_word == "YES":
                print("  PASS: server reports having the plugin")
            else:
                print("  FAIL: expected plugin but response doesn't start with YES")
                ok = False
        else:
            if first_word == "NO":
                print("  PASS: server reports no plugin")
            else:
                print("  FAIL: expected no plugin but response doesn't start with NO")
                ok = False

    print(f"\n{'='*60}")
    if ok:
        print("All checks passed.")
    else:
        print("Some checks FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
