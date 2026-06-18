# Exam answer metadata (`.info` files)

Each exam answer is accompanied by an `aNN.info` file (YAML) written by
[`take_exam.py`](take_exam.py) when that question's agent finishes. It records
exactly how the answer was produced — the model and tools, timing, token usage
and cost, and a verbatim snapshot of the agent's session — so runs are
reproducible and comparable. A run-level [`manifest.yaml`](README.md) summarizes
all questions in a batch using a subset of these same fields.

Values below are taken from a real run (`a01`, sonnet/medium/noskills) for
illustration.

## Identity & status

| Field | Example | Meaning |
| --- | --- | --- |
| `question` | `q01_basics` | Stem of the source question file (`questions/q01_basics.md`). |
| `qid` | `q01` | Question id. |
| `answer_id` | `a01` | Answer id (`qNN` → `aNN`); the filename stem for `.md`/`.log`/`.info`. |
| `stem` | `a01` | The shared filename stem for this question's outputs. |
| `status` | `completed` | Outcome of the run — see [Status values](#status-values). |
| `error` | `null` | Exception message if `status: failed`, else `null`. |

## Configuration

What the agent was set up with. The `tools` booleans are the *requested* config;
the actual tool list the agent received is under [`init`](#init-sdk-session-snapshot).

| Field | Example | Meaning |
| --- | --- | --- |
| `model` | `sonnet` | Friendly model name used in the run-directory name. |
| `model_id` | `claude-sonnet-4-6` | Pinned/expected full model id for `model`. |
| `model_arg` | `sonnet` | The exact string passed to the SDK (alias or full id). |
| `effort` | `medium` | Reasoning effort: `low` / `medium` / `high` / `max`. |
| `config` | `noskills` | The `<config>` label in the run-directory name. |
| `tools.python_execution` | `true` | Always `true` — the agent can run code (Bash + the project venv). |
| `tools.web_search` | `false` | Whether `WebSearch`/`WebFetch` were allowed (`--web-search`). |
| `tools.starsim_ai_plugin` | `false` | Whether the `starsim-ai` plugin (skills + Context7 docs) was loaded (`--plugin`). |
| `context_1m` | `true` | Whether the 1M-token context beta was enabled. |
| `permission_mode` | `bypassPermissions` | Tool-permission mode (unattended; no prompts). |
| `max_turns` | `null` | Per-question agent-loop cap; `null` = unlimited. |
| `max_budget_usd` | `null` | Per-question USD safety cap; `null` = none. |
| `slug` | `jun13.0806` | Session slug (start time) shared by all questions in the batch. |

## Timing

| Field | Example | Meaning |
| --- | --- | --- |
| `start_time` | `2026-06-13T08:06:58` | Local time the agent started (after acquiring a concurrency slot). |
| `end_time` | `2026-06-13T08:15:42` | Local time the agent finished and files were written. |
| `elapsed_seconds` | `524.0` | **Authoritative** wall-clock duration, measured by the runner. |
| `elapsed_human` | `8m44s` | `elapsed_seconds` formatted as `HhMMmSSs`. |
| `duration_ms` | `10745` | Total duration **as reported by the SDK** result message (ms). |
| `duration_api_ms` | `602134` | Time in API calls **as reported by the SDK** (ms). |

> **Note on `duration_*`.** These come straight from the SDK's result message
> and reflect *its* accounting, which can diverge from `elapsed_seconds` — e.g.
> when the agent delegates work to a sub-agent (the `Task` tool) or makes
> overlapping API calls, `duration_api_ms` can even exceed wall-clock time. Use
> `elapsed_seconds` as the real run time.

## Tokens & cost

| Field | Example | Meaning |
| --- | --- | --- |
| `total_cost_usd` | `2.46` | Total cost in USD, as computed by the SDK. |
| `usage_summary.input_tokens` | `3` | Non-cached input tokens. |
| `usage_summary.output_tokens` | `573` | Generated output tokens. |
| `usage_summary.cache_creation_input_tokens` | `2147` | Tokens written to the prompt cache. |
| `usage_summary.cache_read_input_tokens` | `59083` | Tokens read from the prompt cache (cheaper). |
| `usage_summary.total_tokens` | `61806` | Sum of the four counts above (a convenience total). |
| `usage` | *(nested)* | The **raw** usage dict from the SDK; superset of `usage_summary`. |

The raw `usage` block may also include:

| Field | Meaning |
| --- | --- |
| `usage.server_tool_use.web_search_requests` | Number of server-side web searches performed. |
| `usage.server_tool_use.web_fetch_requests` | Number of server-side web fetches performed. |
| `usage.service_tier` | API service tier used (e.g. `standard`). |
| `usage.cache_creation.ephemeral_5m_input_tokens` | Cache writes to the 5-minute TTL cache. |
| `usage.cache_creation.ephemeral_1h_input_tokens` | Cache writes to the 1-hour TTL cache. |
| `usage.speed` | API speed tier reported by the SDK. |

> Token totals reflect the **whole agent loop** (every turn and tool round-trip,
> including cache traffic), not just the final answer. With prompt caching, a
> large `cache_read_input_tokens` is normal and keeps cost down.

## Activity

| Field | Example | Meaning |
| --- | --- | --- |
| `is_error` | `false` | Whether the SDK flagged the result as an error. |
| `result_subtype` | `success` | SDK result subtype: `success`, or an error kind (e.g. `error_max_turns`, `error_max_budget`). |
| `num_turns` | `1` | Conversation turns reported by the SDK (small if the agent delegates via `Task`). |
| `n_tool_uses` | `50` | Total tool calls observed in the agent's stream. |
| `tool_use_counts` | `{Bash: 48, …}` | Per-tool call counts (MCP tools appear by full name). |
| `thinking_chars` | `3697` | Total characters of extended-thinking text produced. |
| `answer_chars` | `16647` | Character length of the final answer written to `aNN.md`. |

## Output files & paths

All paths are relative to the run directory
(`exam/answers/<slug>_<model>-<effort>-<config>/`).

| Field | Example | Meaning |
| --- | --- | --- |
| `answer_file` | `a01.md` | The graded answer file. |
| `log_file` | `a01.log` | The full transcript. |
| `info_file` | `a01.info` | This metadata file. |
| `workspace` | `workspaces/a01` | The agent's scratch directory (its `.py` files, figures, working `answer.md`). |
| `session_id` | `fe024cba-…` | The SDK session id (also in `init`); useful for resuming/tracing. |

## Environment

| Field | Example | Meaning |
| --- | --- | --- |
| `starsim_version` | `3.3.4` | Starsim version installed in the venv the agent used. |
| `python_version` | `3.12.3` | Python version of that environment. |

## `init`: SDK session snapshot

`init` is a **verbatim copy of the SDK's `system`/`init` event** captured at
startup, recorded for provenance. Its sub-fields are the SDK's (not the
runner's); the most useful ones:

| Field | Meaning |
| --- | --- |
| `init.model` | The model the CLI actually resolved and used. |
| `init.tools` | The real list of tool names available to the agent. |
| `init.skills` | Skills available (includes `starsim-ai:*` when `--plugin` is on). |
| `init.plugins` | Plugins actually loaded (the `starsim-ai` plugin when `--plugin` is on). |
| `init.mcp_servers` | MCP servers seen. Account-level `claude.ai …` entries show `status: needs-auth` and are **not** usable tools; the plugin's `context7` appears here when loaded. |
| `init.betas` | Active API betas (e.g. `context-1m-2025-08-07`). |
| `init.permissionMode` | Permission mode (mirrors `permission_mode`). |
| `init.cwd` | The agent's working directory (its workspace). |
| `init.claude_code_version` | Version of the bundled Claude Code CLI. |
| `init.apiKeySource` | Where the API key came from (e.g. `ANTHROPIC_API_KEY`). |
| `init.agents`, `init.slash_commands`, `init.output_style`, `init.uuid`, `init.fast_mode_state` | Other SDK session internals, kept for completeness. |

## Status values

| `status` | Meaning |
| --- | --- |
| `completed` | Ran to completion and wrote `answer.md` (copied to `aNN.md`). |
| `completed_with_error` | Finished but the SDK flagged an error (e.g. hit `--max-budget-usd` or `--max-turns`); any partial output is still saved. |
| `no_answer_file` | Finished cleanly but never wrote `answer.md`; the agent's final message was saved as a fallback (the `aNN.md` notes this). |
| `no_answer` | Produced nothing usable; `aNN.md` is a placeholder note. |
| `failed` | An exception was raised during the run; see `error` and the tail of `aNN.log`. |
