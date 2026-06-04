# Architecture

This page explains how the Claude Code A2A server is put together and how the
pieces fit. For a hands-on walkthrough, see the
[Getting Started tutorial](getting-started.md); for the API surface, see the
[API reference](reference/claude_a2a.md).

## Project layout

| Directory | Purpose |
|-----------|---------|
| `claude_a2a/` | Python package: A2A HTTP server + Claude Agent SDK bridge |
| `eval/` | Evaluation harness ([inspect-ai](https://inspect.ai-safety-institute.org.uk/)): prompt and agent benchmarks |
| `problems/` | Evaluation dataset (Markdown source + generated JSONL) and Streamlit browser |
| `analysis/` | Post-evaluation analysis scripts and plotting |
| `tests/` | pytest test suite |
| `starsim_ai/` | Git submodule: [Starsim AI plugin](https://github.com/starsimhub/starsim_ai) (mounted into Docker for plugin-enabled agents) |
| `logs/` | Evaluation run logs (`.eval` files, gitignored) |

## Claude Code A2A server

The project includes an [A2A](https://google.github.io/A2A/) (Agent-to-Agent)
server that exposes Claude Code as a discoverable, callable coding agent over
HTTP.

**Server** (`claude_a2a/claude_code_server.py`): Builds an Agent Card
advertising four skills — code generation, code review & bug fixing, shell &
DevOps, and research & exploration — and serves it via a Starlette/Uvicorn
application.

**Executor** (`claude_a2a/claude_code_executor.py`): Bridges the A2A protocol to
Claude Code via the Claude Agent SDK. Key behaviors:

- **Workspace isolation** — each A2A task gets its own workspace directory for file operations.
- **Multi-turn sessions** — tracks Claude Agent SDK session IDs per task so follow-up messages resume the same conversation context.
- **Streaming progress** — emits intermediate `TaskStatusUpdateEvent`s as Claude works, including text output and tool-use notifications.
- **Cancellation** — supports async cancellation via `asyncio.Event`.
- **Configurable tools** — defaults to Read, Write, Edit, MultiEdit, Bash, Glob, Grep, and WebSearch; runs with `bypassPermissions` mode.
- **MCP extensibility** — pluggable MCP servers for domain-specific capabilities (an example "secret" server is included in `claude_a2a/mcp_secret.py`).
- **Plugin support** — load Claude Code plugins via `--plugin-dir` (or `PLUGIN_DIRS` env var). The plugin-enabled Docker services use this to mount the Starsim plugin from the `starsim_ai` submodule.
- **Execution logging** — optional structured JSONL logs capturing prompts, tool usage, assistant responses, and errors for each task (see [Execution logging](execution-logging.md)).

### Request lifecycle

For every incoming A2A message, the executor:

1. Extracts the user's text from the A2A `Message` parts.
2. Determines or creates a per-task workspace directory.
3. Calls `claude_agent_sdk.query()` with the configured options.
4. Streams progress back as `TaskStatusUpdateEvent`s.
5. Emits the final answer (and a usage summary) as `TaskArtifactUpdateEvent`s.
6. Records the Claude session ID so subsequent messages on the same A2A task
   resume the conversation.

Configuration is centralized in
[`ClaudeCodeConfig`][claude_a2a.claude_code_executor.ClaudeCodeConfig], which the
[`ClaudeCodeExecutor`][claude_a2a.claude_code_executor.ClaudeCodeExecutor]
consumes.
