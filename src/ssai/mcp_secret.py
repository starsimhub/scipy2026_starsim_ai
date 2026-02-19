"""
FastMCP server that exposes a single "get_secret" tool.

Run standalone:
    python -m sandbagging_workshop.mcp_secret
"""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("secret-server")


@mcp.tool()
def get_secret() -> str:
    """Return the secret word."""
    return "sauce"


if __name__ == "__main__":
    mcp.run()
