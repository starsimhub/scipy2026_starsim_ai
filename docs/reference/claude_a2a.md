# API reference: `claude_a2a`

The `claude_a2a` package implements the Claude Code A2A (Agent-to-Agent) server.
For a conceptual overview, see [Architecture](../architecture.md).

## Executor

::: claude_a2a.claude_code_executor
    options:
      members:
        - ClaudeCodeConfig
        - ClaudeCodeExecutor
        - ExecutionLogger
        - SessionTracker
        - extract_user_text
        - new_agent_text_message

## Server

::: claude_a2a.claude_code_server
    options:
      members:
        - build_agent_card
        - main
