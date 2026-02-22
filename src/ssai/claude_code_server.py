"""
A2A server that exposes Claude Code as a discoverable, callable agent.

Run:
    python -m claude_code_a2a
    python -m claude_code_a2a --port 9999 --workspace ./my-project
"""

from __future__ import annotations

import logging
import os
import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from ssai.claude_code_executor import ClaudeCodeConfig, ClaudeCodeExecutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)


# ---------------------------------------------------------------------------
# Agent Card: describes what this agent can do
# ---------------------------------------------------------------------------

def build_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="Claude Code Agent",
        description=(
            "An autonomous coding agent powered by Anthropic's Claude. "
            "Reads, writes, and edits files, runs shell commands, searches "
            "the web, and builds complete software solutions."
        ),
        url=f"http://{host}:{port}/",
        version="0.1.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=False,
        ),
        skills=[
            AgentSkill(
                id="code_generation",
                name="Code Generation",
                description=(
                    "Generate, scaffold, and write complete code projects "
                    "from natural-language descriptions."
                ),
                tags=["code", "generation", "scaffold", "write"],
                examples=[
                    "Create a Python FastAPI server with user auth",
                    "Build a React dashboard component with charts",
                    "Write a CLI tool that converts CSV to JSON",
                ],
            ),
            AgentSkill(
                id="code_review",
                name="Code Review & Bug Fixing",
                description=(
                    "Analyze existing code for bugs, security issues, "
                    "and quality improvements, then apply fixes."
                ),
                tags=["review", "bugs", "security", "refactor"],
                examples=[
                    "Review my auth module for security vulnerabilities",
                    "Find and fix the failing tests in this project",
                    "Refactor this function to be more maintainable",
                ],
            ),
            AgentSkill(
                id="shell_commands",
                name="Shell & DevOps",
                description=(
                    "Run shell commands, manage files, install "
                    "dependencies, and automate DevOps tasks."
                ),
                tags=["shell", "bash", "devops", "automation"],
                examples=[
                    "Set up a Python virtual environment and install deps",
                    "Find all TODO comments across the project",
                    "Run the test suite and summarize failures",
                ],
            ),
            AgentSkill(
                id="research",
                name="Research & Exploration",
                description=(
                    "Search the web and read documentation to answer "
                    "technical questions and inform implementation."
                ),
                tags=["search", "research", "docs"],
                examples=[
                    "What's the recommended way to handle auth in Next.js 15?",
                    "Find the API docs for the Stripe Checkout SDK",
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

@click.command()
@click.option("--host", default="0.0.0.0", help="Bind address")
@click.option("--port", default=9100, type=int, help="Port to listen on")
@click.option(
    "--workspace",
    default=None,
    help="Root directory for per-task workspaces (default: temp dir)",
)
@click.option(
    "--model",
    default=None,
    help="Claude model to use (e.g. claude-sonnet-4-5-20250929)",
)
@click.option(
    "--max-turns",
    default=None,
    type=int,
    help="Max agent loop turns per request",
)
@click.option(
    "--mcp",
    "mcp_servers",
    multiple=True,
    help="MCP server name to enable (repeatable, e.g. --mcp secret)",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Print detailed Claude execution progress to stdout",
)
@click.option(
    "--log-dir",
    default=None,
    help="Directory for structured JSONL execution logs (one file per task)",
)
@click.option(
    "--run-id",
    default=None,
    help="Label for this server run (subdirectory under log-dir, default: ISO-8601 timestamp)",
)
def main(
    host: str,
    port: int,
    workspace: str | None,
    model: str | None,
    max_turns: int | None,
    mcp_servers: tuple[str, ...],
    verbose: bool,
    log_dir: str | None,
    run_id: str | None,
):
    """Start the Claude Code A2A server."""

    model = model or os.environ.get("CLAUDE_MODEL") or None

    config = ClaudeCodeConfig(
        workspace_root=workspace,
        model=model,
        max_turns=max_turns,
        mcp_servers=list(mcp_servers) if mcp_servers else None,
        verbose=verbose,
        log_dir=log_dir,
        run_id=run_id,
    )

    executor = ClaudeCodeExecutor(config=config)
    agent_card = build_agent_card(host, port)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    click.echo(f"🚀 Claude Code A2A server starting on http://{host}:{port}")
    click.echo(f"📋 Agent Card → http://{host}:{port}/.well-known/agent.json")
    click.echo(f"📁 Workspaces → {config.workspace_root}")
    if config.log_dir and executor._exec_logger:
        click.echo(f"📝 Execution logs → {executor._exec_logger.run_dir}")

    uvicorn.run(app.build(), host=host, port=port)


if __name__ == "__main__":
    main()