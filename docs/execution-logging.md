# Execution logging

When `--log-dir` is set (or `LOG_DIR` in Docker), the executor writes one JSONL
file per task, organized by server run:

```text
agent_logs/
├── 20260221T153000Z/      # first eval run
│   ├── <task_id_1>.jsonl
│   └── <task_id_2>.jsonl
└── 20260221T170000Z/      # second eval run
    ├── <task_id_3>.jsonl
    └── <task_id_4>.jsonl
```

Each server start creates a new timestamped subdirectory. You can also pass
`--run-id` (or `RUN_ID` env var) to label runs explicitly (e.g.
`--run-id baseline-sonnet`).

Each line is a self-contained JSON object. All events include `ts` (Unix
timestamp), `run_id`, and `event` fields.

## Events logged

| Event | Fields | Description |
|-------|--------|-------------|
| `task_start` | `prompt`, `workspace`, `model` | The problem sent to Claude and execution context |
| `assistant_text` | `text` | Each text block Claude produces |
| `tool_use` | `tool`, `input` | Tool name and input summary |
| `result` | `session_id` | Session ID for multi-turn tracking |
| `error` | `error` | Exception details on failure |
| `task_complete` | `response_len` | Final response length |

The directory structure and event schema are implemented by
[`ExecutionLogger`][claude_a2a.claude_code_executor.ExecutionLogger].

## Docker log access

```bash
# Copy logs from a service
docker compose cp sonnet:/home/agent/agent_logs ./sonnet_logs
docker compose cp sonnet-plugin:/home/agent/agent_logs ./sonnet_plugin_logs

# List runs
docker compose exec sonnet ls /home/agent/agent_logs/

# Label a run explicitly
RUN_ID=baseline-sonnet docker compose up --build

# Disable logging
LOG_DIR= docker compose up --build
```
