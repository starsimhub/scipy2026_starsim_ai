"""
AgentExecutor that wraps the Claude Agent SDK to expose Claude Code
capabilities over the A2A protocol.

Handles:
  - One-shot message/send requests
  - Streaming message/sendStream with progress updates
  - Multi-turn conversations via Claude session resumption
  - File artifacts produced by Claude
  - Cancellation
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Artifact,
    FilePart,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Live console output  (visible in Docker logs via stdout)
# ---------------------------------------------------------------------------

_verbose_enabled: bool = False


def _log_to_console(tag: str, message: str, task_id: str | None = None) -> None:
    """Print a formatted line to stdout so operators can watch progress."""
    if not _verbose_enabled:
        return
    prefix = f"[task={task_id}] " if task_id else ""
    # Truncate very long messages to keep logs readable
    if len(message) > 500:
        message = message[:500] + "…"
    print(f"  {prefix}{tag}: {message}", flush=True)


# ---------------------------------------------------------------------------
# MCP server registry
# ---------------------------------------------------------------------------

MCP_REGISTRY: dict[str, dict[str, Any]] = {
    "secret": {
        "type": "stdio",
        "command": "python",
        "args": ["-m", "ssai.mcp_secret"],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_user_text(context: RequestContext) -> str:
    """Pull the concatenated text from the incoming A2A message parts."""
    parts = []
    if context.message and context.message.parts:
        for part in context.message.parts:
            # part.root can be TextPart, FilePart, DataPart, etc.
            if isinstance(part.root, TextPart):
                parts.append(part.root.text)
            elif isinstance(part.root, FilePart):
                # For file uploads, mention the filename so Claude knows
                name = getattr(part.root, "name", "uploaded_file")
                parts.append(f"[Attached file: {name}]")
    return "\n".join(parts) if parts else ""


def new_agent_text_message(text: str, final: bool = True) -> Message:
    """Convenience: create an A2A Message from the agent role."""
    return Message(
        role=Role.agent,
        parts=[Part(root=TextPart(text=text))],
        messageId=str(uuid4()),
        final=final,
    )


# ---------------------------------------------------------------------------
# Execution logger  (structured JSONL logs for later analysis)
# ---------------------------------------------------------------------------

class ExecutionLogger:
    """Writes structured JSONL logs for each task execution.

    Logs are organized by server run:
    ``<log_dir>/<run_id>/<task_id>.jsonl``.

    Each server start creates a new run directory (ISO-8601 timestamp by
    default), so consecutive eval runs are cleanly separated.  A custom
    *run_id* can be passed to label runs explicitly.

    Every line is a self-contained JSON object with at least
    ``{"ts": ..., "run_id": ..., "event": ...}``.
    """

    def __init__(self, log_dir: Path, run_id: str | None = None):
        self.run_id = run_id or datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
        self.run_dir = log_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, task_id: str) -> Path:
        safe_id = task_id.replace("/", "_").replace("..", "_")
        return self.run_dir / f"{safe_id}.jsonl"

    def log(self, task_id: str, event: str, **data: Any) -> None:
        record = {"ts": time.time(), "run_id": self.run_id,
                  "event": event, **data}
        with open(self._path_for(task_id), "a") as f:
            f.write(json.dumps(record, default=str) + "\n")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class ClaudeCodeConfig:
    """
    Knobs for the Claude Code ↔ A2A bridge.

    Attributes:
        workspace_root:  Parent dir where per-task workspaces are created.
                         Defaults to a temp directory.
        system_prompt:   Injected as the Claude Agent system prompt.
        allowed_tools:   Which Claude built-in tools to permit.
        permission_mode: How file/command permissions are handled.
                         Use "acceptEdits" or "bypassPermissions" for
                         unattended A2A operation.
        model:           Model to use (None = SDK default).
        max_turns:       Max agent loop iterations per request.
        verbose:         Print detailed execution progress to stdout.
        log_dir:         Directory for structured JSONL execution logs.
                         One file per task. None = logging disabled.
        run_id:          Label for this server run (used as subdirectory
                         under log_dir). Defaults to an ISO-8601 timestamp.
    """

    def __init__(
        self,
        workspace_root: str | Path | None = None,
        system_prompt: str | None = None,
        allowed_tools: list[str] | None = None,
        permission_mode: str = "bypassPermissions",
        model: str | None = None,
        max_turns: int | None = None,
        mcp_servers: list[str] | None = None,
        verbose: bool = False,
        log_dir: str | Path | None = None,
        run_id: str | None = None,
    ):
        self.workspace_root = Path(
            workspace_root or tempfile.mkdtemp(prefix="claude_a2a_")
        )
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        self.system_prompt = system_prompt or (
            "You are a coding agent exposed via the A2A protocol. "
            "Complete the user's request thoroughly. "
            "When you produce files, mention their paths explicitly."
        )
        self.allowed_tools = allowed_tools or [
            "Read", "Write", "Edit", "MultiEdit",
            "Bash", "Glob", "Grep", "WebSearch",
        ]
        self.permission_mode = permission_mode
        self.model = model
        self.max_turns = max_turns
        self.mcp_servers = mcp_servers or []
        self.verbose = verbose
        self.log_dir = Path(log_dir) if log_dir else None
        self.run_id = run_id

        # Set module-level flag so _log_to_console can check it
        global _verbose_enabled
        _verbose_enabled = verbose


# ---------------------------------------------------------------------------
# Session tracker  (taskId → Claude session_id for multi-turn)
# ---------------------------------------------------------------------------

class SessionTracker:
    """Maps A2A task IDs to Claude Agent SDK session IDs for resume."""

    def __init__(self):
        self._sessions: dict[str, str] = {}

    def get(self, task_id: str) -> str | None:
        return self._sessions.get(task_id)

    def set(self, task_id: str, session_id: str) -> None:
        self._sessions[task_id] = session_id

    def remove(self, task_id: str) -> None:
        self._sessions.pop(task_id, None)


# ---------------------------------------------------------------------------
# The A2A AgentExecutor
# ---------------------------------------------------------------------------

class ClaudeCodeExecutor(AgentExecutor):
    """
    Bridges the A2A protocol to Claude Code via the Claude Agent SDK.

    For every incoming A2A message:
      1. Extract the user's text from the A2A Message parts.
      2. Determine or create a per-task workspace directory.
      3. Call claude_agent_sdk.query() with appropriate options.
      4. Stream progress as TaskStatusUpdateEvents.
      5. Emit the final answer as a TaskArtifactUpdateEvent.
      6. Track the Claude session ID so subsequent messages on the
         same A2A task resume the conversation.
    """

    def __init__(self, config: ClaudeCodeConfig | None = None):
        super().__init__()
        self.config = config or ClaudeCodeConfig()
        self.sessions = SessionTracker()
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._exec_logger: ExecutionLogger | None = (
            ExecutionLogger(self.config.log_dir, self.config.run_id)
            if self.config.log_dir else None
        )

    # ----- workspace management -----

    def _workspace_for_task(self, task_id: str | None) -> Path:
        """Return (and create) a workspace directory for a given task."""
        folder_name = task_id or str(uuid4())
        ws = self.config.workspace_root / folder_name
        ws.mkdir(parents=True, exist_ok=True)
        return ws

    # ----- build SDK options -----

    def _build_options(
        self, task_id: str | None, workspace: Path
    ) -> ClaudeAgentOptions:
        opts = ClaudeAgentOptions(
            system_prompt=self.config.system_prompt,
            allowed_tools=self.config.allowed_tools,
            permission_mode=self.config.permission_mode,
            cwd=str(workspace),
        )
        if self.config.model:
            opts.model = self.config.model
        if self.config.max_turns:
            opts.max_turns = self.config.max_turns

        # Attach requested MCP servers
        if self.config.mcp_servers:
            mcp_configs: dict[str, Any] = {}
            mcp_tools: list[str] = []
            for name in self.config.mcp_servers:
                if name not in MCP_REGISTRY:
                    logger.warning("Unknown MCP server %r – skipping", name)
                    continue
                mcp_configs[name] = MCP_REGISTRY[name]
                mcp_tools.append(f"mcp__{name}__*")
            if mcp_configs:
                opts.mcp_servers = mcp_configs
                opts.allowed_tools = list(opts.allowed_tools or []) + mcp_tools

        # Resume an existing Claude session for multi-turn
        if task_id:
            session_id = self.sessions.get(task_id)
            if session_id:
                opts.resume = session_id
                opts.continue_conversation = True

        return opts

    # ----- A2A execute -----

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_text = extract_user_text(context)
        if not user_text:
            await event_queue.enqueue_event(
                new_agent_text_message("I didn't receive any input. Could you send a message?")
            )
            return

        task_id = context.task_id
        context_id = context.context_id or ""
        workspace = self._workspace_for_task(task_id)

        # Set up cancellation signal
        cancel_event = asyncio.Event()
        if task_id:
            self._cancel_events[task_id] = cancel_event

        # Structured execution log
        elog = self._exec_logger
        if elog and task_id:
            elog.log(task_id, "task_start", prompt=user_text,
                     workspace=str(workspace), model=self.config.model)

        logger.info(
            "Claude Code executing | task=%s workspace=%s prompt_len=%d",
            task_id, workspace, len(user_text),
        )
        if self.config.verbose:
            print(f"\n{'='*60}", flush=True)
            print(f"  CLAUDE CODE START | task={task_id}", flush=True)
            print(f"  Prompt: {user_text[:200]}{'…' if len(user_text) > 200 else ''}", flush=True)
            print(f"{'='*60}", flush=True)

        # Signal that we're working
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                taskId=task_id or "",
                contextId=context_id,
                status=TaskStatus(
                    state=TaskState.working,
                    message=new_agent_text_message(
                        "Claude Code is working on your request…",
                        final=False,
                    ),
                ),
                final=False,
            )
        )

        opts = self._build_options(task_id, workspace)
        collected_text: list[str] = []
        session_id: str | None = None

        try:
            async for msg in query(prompt=user_text, options=opts):
                # Check for cancellation
                if cancel_event.is_set():
                    logger.info("Task %s cancelled during execution", task_id)
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            taskId=task_id or "",
                            contextId=context_id,
                            status=TaskStatus(state=TaskState.canceled),
                            final=True,
                        )
                    )
                    return

                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock) and block.text:
                            collected_text.append(block.text)
                            _log_to_console("ASSISTANT", block.text, task_id)
                            if elog and task_id:
                                elog.log(task_id, "assistant_text",
                                         text=block.text)

                            # Emit intermediate streaming update
                            await event_queue.enqueue_event(
                                TaskStatusUpdateEvent(
                                    taskId=task_id or "",
                                    contextId=context_id,
                                    status=TaskStatus(
                                        state=TaskState.working,
                                        message=new_agent_text_message(
                                            block.text, final=False
                                        ),
                                    ),
                                    final=False,
                                )
                            )

                        elif isinstance(block, ToolUseBlock):
                            # Log tool use with input summary
                            tool_input = getattr(block, "input", None)
                            input_summary = ""
                            if isinstance(tool_input, dict):
                                input_summary = json.dumps(tool_input, default=str)
                            elif tool_input is not None:
                                input_summary = str(tool_input)
                            _log_to_console(
                                "TOOL_USE",
                                f"{block.name}({input_summary})",
                                task_id,
                            )
                            if elog and task_id:
                                elog.log(task_id, "tool_use",
                                         tool=block.name,
                                         input=input_summary)

                            # Notify the caller which tool Claude is using
                            tool_msg = f"🔧 Using tool: {block.name}"
                            await event_queue.enqueue_event(
                                TaskStatusUpdateEvent(
                                    taskId=task_id or "",
                                    contextId=context_id,
                                    status=TaskStatus(
                                        state=TaskState.working,
                                        message=new_agent_text_message(
                                            tool_msg, final=False
                                        ),
                                    ),
                                    final=False,
                                )
                            )

                elif isinstance(msg, ResultMessage):
                    # Capture the session ID for multi-turn
                    session_id = getattr(msg, "session_id", None)
                    _log_to_console("RESULT", f"session_id={session_id}", task_id)
                    if elog and task_id:
                        elog.log(task_id, "result",
                                 session_id=session_id)

                else:
                    _log_to_console("MSG", f"{type(msg).__name__}", task_id)

        except Exception as exc:
            logger.exception("Claude Code execution failed for task %s", task_id)
            if elog and task_id:
                elog.log(task_id, "error", error=str(exc))
            if self.config.verbose:
                print(f"  ERROR | task={task_id}: {exc}", flush=True)
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=task_id or "",
                    contextId=context_id,
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=new_agent_text_message(
                            f"Execution error: {exc}"
                        ),
                    ),
                    final=True,
                )
            )
            return
        finally:
            if task_id:
                self._cancel_events.pop(task_id, None)

        # Store session for multi-turn
        if task_id and session_id:
            self.sessions.set(task_id, session_id)

        # Log completion
        final_text = "\n".join(collected_text) if collected_text else "Done."
        if elog and task_id:
            elog.log(task_id, "task_complete",
                     response_len=len(final_text))

        # Emit the final result as an artifact
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                taskId=task_id or "",
                contextId=context_id,
                artifact=Artifact(
                    artifactId=str(uuid4()),
                    parts=[Part(root=TextPart(text=final_text))],
                    name="claude_code_response",
                    lastChunk=True,
                ),
                append=False,
            )
        )

        # Mark task as completed
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                taskId=task_id or "",
                contextId=context_id,
                status=TaskStatus(state=TaskState.completed),
                final=True,
            )
        )

        if self.config.verbose:
            print(f"{'='*60}", flush=True)
            print(f"  CLAUDE CODE DONE | task={task_id} | response_len={len(final_text)}", flush=True)
            print(f"{'='*60}\n", flush=True)

        logger.info(
            "Claude Code completed | task=%s response_len=%d",
            task_id, len(final_text),
        )

    # ----- A2A cancel -----

    @override
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task_id = context.task_id
        context_id = context.context_id or ""
        cancel_event = self._cancel_events.get(task_id or "")
        if cancel_event:
            cancel_event.set()
            logger.info("Cancel signal sent for task %s", task_id)
        else:
            # Task isn't currently running; mark it cancelled anyway
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=task_id or "",
                    contextId=context_id,
                    status=TaskStatus(state=TaskState.canceled),
                    final=True,
                )
            )