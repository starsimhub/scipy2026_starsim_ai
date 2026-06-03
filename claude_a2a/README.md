# claude_a2a

Main source package for the Claude Code A2A (Agent-to-Agent) server.

## Modules

| File | Purpose |
|------|---------|
| `claude_code_server.py` | A2A HTTP server that exposes Claude Code as a discoverable agent. Entry point for the `start-claude-code-server` CLI. |
| `claude_code_executor.py` | Bridges the A2A protocol to the Claude Agent SDK. Contains `ClaudeCodeConfig` (configuration) and `ClaudeCodeExecutor` (task execution). |
| `check_a2a_servers.py` | Health-check utility for verifying running A2A server instances. |
| `mcp_secret.py` | Example MCP (Model Context Protocol) server used for evaluation. |

## How it fits together

1. `claude_code_server.py` starts an HTTP server and registers an `AgentCard` describing capabilities.
2. Incoming A2A requests are routed to `ClaudeCodeExecutor`, which spawns a Claude Agent SDK session in an isolated workspace.
3. The executor streams results back through the A2A protocol.
