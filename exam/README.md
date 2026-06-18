# Starsim exam

A practical, ~3-hour exam that probes how well an AI agent can use Starsim. It
has two halves:

1. **Exam-taker** (`take_exam.py`) — autonomous agents answer the questions.
   **Implemented.**
2. **Exam-marker** — autonomous agents grade the answers against a marking
   scheme. **Planned (not yet implemented).**

```text
exam/
├── questions/                 # the exam (source of truth)
│   ├── exam_instructions.md
│   └── qNN_*.md               # one file per question (q01–q04)
├── answers/                   # generated; one subdir per run
│   └── <slug>_<model>-<effort>-<config>/   # e.g. jun13.0740_sonnet-medium-noskills
│       ├── aNN.md             # graded answer
│       ├── aNN.log            # full transcript
│       ├── aNN.info           # run metadata (YAML)
│       ├── workspaces/aNN/    # agent scratch + figures
│       └── manifest.yaml      # batch summary
├── take_exam.py
├── metadata.md                # field-by-field reference for .info files
└── README.md
```

## Exam-taker

`take_exam.py` launches **one autonomous agent per question, in parallel**
(four agents for `q01`–`q04`). Each agent:

- has a Python environment and **must run code** to develop and verify answers
  (`Bash`, `Read`, `Write`, `Edit`, … are always available);
- optionally has **web search** and/or the **`starsim-ai` plugin** (Starsim
  skills + Context7 docs), per flags;
- runs **to completion with no turn limit by default** (may take 1 hr+ each);
- writes its answer, a full transcript, and metadata to disk.

### Usage

Always run via `uv` so the agent's `python` resolves to the project venv (where
Starsim is installed):

```bash
# Baseline: closed-book apart from running code (no web, no plugin)
uv run python exam/take_exam.py --model sonnet --effort medium

# Open-book: web search + starsim-ai plugin, high effort, opus
uv run python exam/take_exam.py --model opus --effort high --web-search --plugin

# A subset of questions on a cheap model, with a custom <config> tag
uv run python exam/take_exam.py --questions q01,q03 --model haiku \
    --effort low --plugin --config skills-only

# Preview the plan without spending anything
uv run python exam/take_exam.py --model opus --effort high --plugin --dry-run
```

### Key options

| Flag | Default | Meaning |
| --- | --- | --- |
| `--model` | `sonnet` | `haiku` / `sonnet` / `opus`, or a full model id |
| `--effort` | `medium` | `low` / `medium` / `high` / `max` |
| `--web-search` / `--no-web-search` | off | Allow `WebSearch` / `WebFetch` |
| `--plugin` / `--no-plugin` | off | Load the `starsim-ai` plugin |
| `--config` | derived | Filename tag; default `noskills`/`web`/`skills`/`full` |
| `--context-1m` / `--no-context-1m` | auto | 1M-token context; on for sonnet/opus, off for haiku |
| `--questions` | `all` | Comma list, e.g. `q01,q03` |
| `--max-turns` | unlimited | Safety cap on agent loop iterations |
| `--max-budget-usd` | none | Per-question USD safety cap |
| `--max-concurrency` | one per question | Throttle parallel agents |
| `--heartbeat` | `30` | Seconds between live progress snapshots (0 to disable) |
| `--slug` | start time | Override the run subdirectory name |
| `--verbose` / `-v` | off | Stream assistant text and tool calls |
| `--dry-run` | off | Print the plan and exit |

Run `uv run python exam/take_exam.py --help` for the full list.

### Following progress

You don't have to wait for agents to finish — progress is live:

- **Heartbeat** (default every 30 s): a console snapshot of each running agent
  (elapsed, tool-call count, last tool, replies). Tune with `--heartbeat N`.
- **`tail -f`** any agent's `.log` (written incrementally) for the full
  transcript: `tail -f exam/answers/<run>/*.log`.
- **`--verbose`** streams assistant text and tool calls as they happen.
- The per-question `workspaces/aNN/` fills with scratch scripts and figures.

Each question's `.md`/`.info` are written the moment that agent finishes;
`manifest.yaml` is written when the whole batch completes.

### Output files

Each run gets a directory `answers/<slug>_<model>-<effort>-<config>/` (e.g.
`answers/jun13.0740_sonnet-medium-noskills/`). For each question, three sibling
files are written there, named by answer id (`q01` → `a01`):

- **`.md`** — the agent's final answer (what gets graded). The agent is
  instructed to write `answer.md` in its workspace; that file is copied here. If
  it never writes one, the final assistant message is captured as a fallback
  (and the status reflects this).
- **`.log`** — the complete transcript: thinking, every tool call with its
  input, and (truncated) tool results.
- **`.info`** — YAML metadata: start/end/elapsed time, token usage, cost, model,
  effort, enabled tools, turn/tool counts, session id, the SDK init snapshot,
  Starsim/Python versions, and status. See [`metadata.md`](metadata.md) for a
  field-by-field reference.

`manifest.yaml` summarizes the whole batch (handy for the future marker).
Per-question scratch work (`.py` scripts, saved figures, the agent's own
`answer.md`) is preserved under `workspaces/aNN/`.

### Notes & caveats

- **Starsim version.** The exam text references Starsim v3.3; agents use whatever
  is installed in the project venv (run `uv sync` / upgrade `starsim` first if
  you need a specific version). The version used is recorded in every `.info`.
- **Figures.** Saved figures live in the per-question `workspaces/aNN/`
  alongside the agent's working copy of `answer.md`; the top-level `aNN.md` is
  the text + code submission, and its code blocks regenerate the figures.
- **Cost.** With no turn limit, an `opus --effort high` run can be long and
  expensive. Use `--max-budget-usd` and/or `--max-turns` as guardrails, and
  start with `--dry-run`.
- **Isolation.** The host's user/project Claude config is not loaded
  (`setting_sources=None`); only explicitly attached tools/plugins are active.
  Account-level `claude.ai` connectors may appear in the `.info` init snapshot as
  `needs-auth`, but they are never usable tools.
- **Running inside Claude Code.** The SDK spawns a Claude Code subprocess, which
  refuses to nest; the script clears the `CLAUDECODE` marker on startup so it
  works either way. For real benchmark runs, launch from an ordinary shell.

## Exam-marker (planned)

A second runner will dispatch one agent per question to grade the generated
answers against a marking scheme, writing scores and rationale. It will key off
`answers/<slug>/manifest.yaml` and the per-answer `.md`/`.info` files.
