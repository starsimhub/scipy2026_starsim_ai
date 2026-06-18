"""
Exam-taking agent for the Starsim AI evaluation.

Launches one autonomous Claude Code agent per exam question (``q01``–``q04``)
and runs them in parallel. Each agent gets a working Python environment (so it
can write and run code to develop and verify its answers) plus a configurable
set of extra tools: web search and/or the ``starsim-ai`` plugin (skills +
Context7 docs). The model and reasoning effort are configurable too.

Each run gets its own directory named ``<slug>_<model>-<effort>-<config>``,
where ``<slug>`` is the session start time (e.g.
``exam/answers/jun13.0740_sonnet-medium-noskills/``). For every question, an
agent writes three sibling files there, named by answer id (``q01`` → ``a01``):

  - ``aNN.md``    — the graded answer (Markdown)
  - ``aNN.log``   — the full transcript (thinking, tool calls, results)
  - ``aNN.info``  — run metadata (YAML: timing, tokens, cost, model, tools…)

Scratch work (the agent's `.py` files, figures, etc.) is preserved under
``workspaces/aNN/`` within the run directory, and a batch-level
``manifest.yaml`` summarizes the whole run for the (separate) marking agent.

Progress is followable live: each agent's ``.log`` is written incrementally
(``tail -f`` it), and a heartbeat prints a per-agent snapshot every 30 s.

Each agent runs to completion with no turn limit by default, which may take an
hour or more per question. Use ``--max-budget-usd`` and/or ``--max-turns`` as
safety valves.

Examples:
    # Baseline: closed-book apart from running code (no web, no plugin)
    uv run python exam/take_exam.py --model sonnet --effort medium

    # Open-book: web search + the starsim-ai plugin, high effort, opus
    uv run python exam/take_exam.py --model opus --effort high --web-search --plugin

    # Just two questions, cheap model, custom config label
    uv run python exam/take_exam.py --questions q01,q03 --model haiku \\
        --effort low --plugin --config skills-only

    # Preview what would run without calling the model
    uv run python exam/take_exam.py --model opus --effort high --plugin --dry-run

Run ``uv run python exam/take_exam.py --help`` for all options.
"""

from __future__ import annotations

# The Claude Agent SDK launches a Claude Code subprocess, which refuses to run
# when it detects it is nested inside another Claude Code session. We are a
# standalone batch runner, so clear the marker before the SDK starts. (Harmless
# when launched from an ordinary shell, where the variable is unset anyway.)
import os
os.environ.pop("CLAUDECODE", None)

import argparse
import asyncio
import json
import platform
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    SdkPluginConfig,
    AssistantMessage,
    UserMessage,
    SystemMessage,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
)

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

EXAM_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EXAM_DIR.parent
DEFAULT_QUESTIONS_DIR = EXAM_DIR / "questions"
DEFAULT_OUTPUT_DIR = EXAM_DIR / "answers"
STARSIM_PLUGIN_DIR = PROJECT_ROOT / "starsim_ai" / "plugins" / "starsim"
INSTRUCTIONS_FILENAME = "exam_instructions.md"

# Friendly model name -> pinned model id (recorded in metadata). The CLI also
# accepts the friendly aliases directly, so unknown values pass straight
# through to the SDK.
MODEL_ALIASES = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-8",
}

VALID_EFFORTS = ("low", "medium", "high", "max")

# Tools toggled by --web-search. Everything else (Read/Write/Edit/Bash/Glob/
# Grep/Skill/TodoWrite/…) is left at the SDK default so the agent can freely
# run and verify code. The starsim-ai plugin's tools (skills + Context7 docs)
# exist only when the plugin is loaded, so it needs no allow/deny entry.
WEB_TOOLS = ("WebSearch", "WebFetch")

# Cap on how much of a single tool result is copied into the .log transcript.
MAX_TOOL_RESULT_CHARS = 20_000

SYSTEM_PROMPT = (
    "You are an expert computational epidemiologist and Python programmer "
    "sitting a timed, practical exam on the Starsim disease-modeling library "
    "(use the version installed in this environment). You have a working "
    "Python environment in which Starsim is installed; you MUST write and run "
    "code to develop and verify every answer — the exam cannot be completed "
    "correctly without executing code.\n\n"
    "Work autonomously and to a high standard. A single question may take an "
    "hour or more: do not rush, and do not stop until you have fully and "
    "correctly answered every sub-part. Treat all code as if submitting a pull "
    "request — clean, idiomatic, runnable Starsim. Rely only on the installed "
    "Starsim package and the tools you have been given; do not read files "
    "outside your working directory."
)

SUBMIT_INSTRUCTIONS = """\
# How to submit your answer

- Use your current working directory as scratch space: write `.py` scripts and
  run them (e.g. `python solve.py`) to develop and verify your code and outputs
  before committing to a final answer. Run things as many times as you need.
- When a sub-part asks for a plot, generate it and save it to a file with
  `plt.savefig(...)` (do NOT call `plt.show()`); reference the saved figure in
  your answer.
- When you are completely finished, write your COMPLETE answer to a single
  Markdown file named exactly `answer.md` in your current working directory.
  The contents of `answer.md` are what will be graded, so it must stand on its
  own and answer every sub-part, following the exam instructions above
  (runnable ```python``` code blocks followed by text explanations).
"""

try:
    import starsim as _ss

    STARSIM_VERSION = getattr(_ss, "__version__", "unknown")
except Exception:  # pragma: no cover - starsim should be installed
    STARSIM_VERSION = "not installed"


# ---------------------------------------------------------------------------
# Configuration data
# ---------------------------------------------------------------------------


@dataclass
class QuestionSpec:
    """A single exam question to be answered."""

    qid: str  # e.g. "q01"
    aid: str  # e.g. "a01"
    title: str  # e.g. "q01_basics"
    path: Path  # path to the question Markdown file


@dataclass
class RunConfig:
    """Shared configuration for a batch of exam-taking agents."""

    model_friendly: str
    model_arg: str  # what is actually passed to the SDK (alias or full id)
    model_id: str  # pinned/expected full id, for metadata
    effort: str
    config_label: str
    web_search: bool
    plugin: bool
    context_1m: bool
    max_turns: int | None
    max_budget_usd: float | None
    slug: str
    output_dir: Path
    instructions: str

    @property
    def run_name(self) -> str:
        """Run directory name: ``<slug>_<model>-<effort>-<config>``."""
        return f"{self.slug}_{self.model_friendly}-{self.effort}-{self.config_label}"

    @property
    def run_dir(self) -> Path:
        """Output directory for this run (created under ``output_dir``)."""
        return self.output_dir / self.run_name


@dataclass
class LiveProgress:
    """Mutable live counters for one agent, read by the heartbeat task."""

    qid: str
    start_perf: float | None = None
    n_tool_uses: int = 0
    n_replies: int = 0
    last_tool: str = ""
    done: bool = False
    status: str = "queued"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_slug(now: datetime | None = None) -> str:
    """Return a filesystem-friendly session slug like ``jun13.0740``."""
    now = now or datetime.now()
    return now.strftime("%b%d.%H%M").lower()


def friendly_model_name(model: str) -> str:
    """Map a model argument to a short, filename-safe friendly name."""
    if model in MODEL_ALIASES:
        return model
    for alias, full in MODEL_ALIASES.items():
        if model == full:
            return alias
    # Unknown full id: sanitize for use in a filename.
    return model.replace("/", "-").replace(":", "-")


def derive_config_label(web_search: bool, plugin: bool) -> str:
    """Default ``<config>`` filename tag derived from the enabled tools."""
    if plugin and web_search:
        return "full"
    if plugin:
        return "skills"
    if web_search:
        return "web"
    return "noskills"


def discover_questions(questions_dir: Path, selected: list[str] | None) -> list[QuestionSpec]:
    """Find ``q*.md`` question files, optionally filtered by id prefix.

    Args:
        questions_dir: Directory containing ``qNN_*.md`` question files.
        selected: Optional list of id prefixes (e.g. ``["q01", "q03"]``); if
            ``None`` or contains ``"all"``, every question is included.

    Returns:
        A sorted list of [`QuestionSpec`][exam.take_exam.QuestionSpec].
    """
    files = sorted(questions_dir.glob("q*.md"))
    if not files:
        raise FileNotFoundError(f"No question files (q*.md) found in {questions_dir}")

    specs: list[QuestionSpec] = []
    for f in files:
        qid = f.stem.split("_")[0]  # "q01_basics" -> "q01"
        aid = "a" + qid[1:] if qid.startswith("q") else qid
        specs.append(QuestionSpec(qid=qid, aid=aid, title=f.stem, path=f))

    if selected and "all" not in selected:
        wanted = {s.lower() for s in selected}
        specs = [s for s in specs if s.qid.lower() in wanted or s.title.lower() in wanted]
        missing = wanted - {s.qid.lower() for s in specs} - {s.title.lower() for s in specs}
        if missing:
            raise ValueError(
                f"Requested questions not found: {sorted(missing)}. "
                f"Available: {[s.qid for s in discover_questions(questions_dir, None)]}"
            )
    return specs


def yaml_safe(obj: Any) -> Any:
    """Coerce arbitrary objects into YAML-serializable plain types."""
    return json.loads(json.dumps(obj, default=str))


def short_tool_name(name: str) -> str:
    """Shorten an MCP tool name (``mcp__server__tool``) to its final segment."""
    if name.startswith("mcp__"):
        return name.split("__")[-1]
    return name


def stringify_tool_result(content: Any) -> str:
    """Render a ToolResultBlock's content (str or list of blocks) as text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text") or json.dumps(item, default=str))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def summarize_usage(usage: dict[str, Any] | None) -> dict[str, int]:
    """Extract the headline token counts from a raw usage dict."""
    if not usage:
        return {}
    keys = (
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
    )
    summary = {k: int(usage.get(k, 0) or 0) for k in keys}
    summary["total_tokens"] = sum(summary.values())
    return summary


def human_duration(seconds: float) -> str:
    """Format a duration in seconds as ``1h02m03s``."""
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


# ---------------------------------------------------------------------------
# Transcript writer
# ---------------------------------------------------------------------------


class Transcript:
    """Append-only, line-buffered transcript writer for a single agent run."""

    def __init__(self, path: Path):
        self.path = path
        self._f = open(path, "w", buffering=1, encoding="utf-8")

    def raw(self, text: str) -> None:
        self._f.write(text)

    def event(self, tag: str, body: str = "") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._f.write(f"\n[{ts}] {tag}\n")
        if body:
            self._f.write(body.rstrip("\n") + "\n")

    def rule(self, title: str) -> None:
        self._f.write(f"\n{'=' * 72}\n{title}\n{'=' * 72}\n")

    def close(self) -> None:
        try:
            self._f.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# SDK options and prompt
# ---------------------------------------------------------------------------


def build_options(cfg: RunConfig, workspace: Path) -> ClaudeAgentOptions:
    """Construct the ClaudeAgentOptions for one exam-taking agent."""
    disallowed = [] if cfg.web_search else list(WEB_TOOLS)
    plugins = (
        [SdkPluginConfig(type="local", path=str(STARSIM_PLUGIN_DIR))]
        if cfg.plugin
        else []
    )

    opts = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        permission_mode="bypassPermissions",
        cwd=str(workspace),
        model=cfg.model_arg,
        effort=cfg.effort,
        disallowed_tools=disallowed,
        plugins=plugins,
        # Headless plotting; never block on an interactive backend.
        env={"MPLBACKEND": "Agg"},
        # Isolation: ignore the host's user/project/local Claude config so the
        # only skills/plugins available are the ones we attach explicitly.
        setting_sources=None,
    )
    if cfg.max_turns:
        opts.max_turns = cfg.max_turns
    if cfg.max_budget_usd:
        opts.max_budget_usd = cfg.max_budget_usd
    if cfg.context_1m:
        opts.betas = ["context-1m-2025-08-07"]
    return opts


def build_prompt(cfg: RunConfig, question: QuestionSpec) -> str:
    """Assemble the user prompt: instructions + question + submit directive."""
    question_text = question.path.read_text(encoding="utf-8").strip()
    return "\n".join(
        [
            "# Exam instructions",
            "",
            cfg.instructions.strip(),
            "",
            "---",
            "",
            "# Your exam question",
            "",
            question_text,
            "",
            "---",
            "",
            SUBMIT_INSTRUCTIONS.strip(),
            "",
        ]
    )


# ---------------------------------------------------------------------------
# Per-question agent run
# ---------------------------------------------------------------------------


async def run_question(
    question: QuestionSpec,
    cfg: RunConfig,
    sem: asyncio.Semaphore,
    verbose: bool,
    prog: LiveProgress,
) -> dict[str, Any]:
    """Run one autonomous agent on one question and write its three files.

    Returns:
        A metadata dict (also written to the ``.info`` YAML file).
    """
    async with sem:
        run_dir = cfg.run_dir
        stem = question.aid  # files are aNN.md / aNN.log / aNN.info
        md_path = run_dir / f"{stem}.md"
        log_path = run_dir / f"{stem}.log"
        info_path = run_dir / f"{stem}.info"
        workspace = run_dir / "workspaces" / stem
        workspace.mkdir(parents=True, exist_ok=True)

        opts = build_options(cfg, workspace)
        prompt = build_prompt(cfg, question)

        tr = Transcript(log_path)
        tr.rule(f"EXAM TRANSCRIPT — {question.title}")
        tr.raw(
            f"question:    {question.title}\n"
            f"model:       {cfg.model_friendly} ({cfg.model_id})\n"
            f"effort:      {cfg.effort}\n"
            f"config:      {cfg.config_label}\n"
            f"web_search:  {cfg.web_search}\n"
            f"plugin:      {cfg.plugin}\n"
            f"context_1m:  {cfg.context_1m}\n"
            f"max_turns:   {cfg.max_turns}\n"
            f"workspace:   {workspace}\n"
        )

        start_dt = datetime.now()
        start_perf = time.perf_counter()
        prog.start_perf = start_perf
        prog.status = "running"
        tr.event("START", start_dt.isoformat(timespec="seconds"))
        print(f"  ▶ {question.qid}: starting → {run_dir.name}/{stem}.md", flush=True)

        # Captured state
        collected_text: list[str] = []
        thinking_chars = 0
        n_tool_uses = 0
        tool_counts: dict[str, int] = {}
        usage: dict[str, Any] = {}
        total_cost_usd: float | None = None
        result_text: str | None = None
        session_id: str | None = None
        is_error = False
        result_subtype: str | None = None
        num_turns: int | None = None
        duration_ms: int | None = None
        duration_api_ms: int | None = None
        init_data: Any = None
        error_str: str | None = None
        status = "completed"

        try:
            async for msg in query(prompt=prompt, options=opts):
                if isinstance(msg, SystemMessage):
                    subtype = getattr(msg, "subtype", None)
                    data = getattr(msg, "data", None)
                    if subtype == "init":
                        init_data = data
                    tr.event(
                        f"SYSTEM/{subtype}",
                        json.dumps(yaml_safe(data), indent=2) if data else "",
                    )

                elif isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ThinkingBlock):
                            thinking_chars += len(block.thinking)
                            tr.event("THINKING", block.thinking)
                        elif isinstance(block, TextBlock):
                            if block.text:
                                collected_text.append(block.text)
                                prog.n_replies += 1
                                tr.event("ASSISTANT", block.text)
                                if verbose:
                                    snippet = block.text.strip().replace("\n", " ")[:100]
                                    print(f"  · {question.qid}: {snippet}", flush=True)
                        elif isinstance(block, ToolUseBlock):
                            n_tool_uses += 1
                            tool_counts[block.name] = tool_counts.get(block.name, 0) + 1
                            prog.n_tool_uses = n_tool_uses
                            prog.last_tool = short_tool_name(block.name)
                            tr.event(
                                f"TOOL_USE · {block.name}",
                                json.dumps(yaml_safe(block.input), indent=2),
                            )
                            if verbose:
                                print(f"  🔧 {question.qid}: {block.name}", flush=True)

                elif isinstance(msg, UserMessage):
                    content = msg.content if isinstance(msg.content, list) else []
                    for block in content:
                        if isinstance(block, ToolResultBlock):
                            text = stringify_tool_result(block.content)
                            if len(text) > MAX_TOOL_RESULT_CHARS:
                                text = (
                                    text[:MAX_TOOL_RESULT_CHARS]
                                    + f"\n…[truncated {len(text) - MAX_TOOL_RESULT_CHARS} chars]"
                                )
                            tag = "TOOL_RESULT (error)" if block.is_error else "TOOL_RESULT"
                            tr.event(tag, text)

                elif isinstance(msg, ResultMessage):
                    usage = msg.usage or {}
                    total_cost_usd = msg.total_cost_usd
                    result_text = msg.result
                    session_id = msg.session_id
                    is_error = msg.is_error
                    result_subtype = msg.subtype
                    num_turns = msg.num_turns
                    duration_ms = msg.duration_ms
                    duration_api_ms = msg.duration_api_ms
                    tr.event(
                        "RESULT",
                        json.dumps(
                            {
                                "subtype": result_subtype,
                                "is_error": is_error,
                                "num_turns": num_turns,
                                "duration_ms": duration_ms,
                                "duration_api_ms": duration_api_ms,
                                "total_cost_usd": total_cost_usd,
                                "usage": yaml_safe(usage),
                            },
                            indent=2,
                        ),
                    )
            if is_error:
                status = "completed_with_error"
        except Exception as exc:  # keep other agents alive
            status = "failed"
            error_str = f"{type(exc).__name__}: {exc}"
            tr.event("EXCEPTION", traceback.format_exc())
            print(f"  ✖ {question.qid}: FAILED — {error_str}", flush=True)

        # ----- resolve the answer -----
        ws_answer = workspace / "answer.md"
        answer_text = ""
        if ws_answer.exists() and ws_answer.stat().st_size > 0:
            answer_text = ws_answer.read_text(encoding="utf-8")
            md_path.write_text(answer_text, encoding="utf-8")
        else:
            fallback = (result_text or "\n".join(collected_text)).strip()
            if fallback:
                if status == "completed":
                    status = "no_answer_file"
                answer_text = fallback
                md_path.write_text(
                    "<!-- NOTE: the agent did not write answer.md; this is its "
                    "final assistant message, captured as a fallback. -->\n\n"
                    + fallback
                    + "\n",
                    encoding="utf-8",
                )
            else:
                if status == "completed":
                    status = "no_answer"
                md_path.write_text(
                    "<!-- NOTE: the agent produced no answer. -->\n", encoding="utf-8"
                )

        # ----- timing + metadata -----
        end_dt = datetime.now()
        elapsed = time.perf_counter() - start_perf
        tr.event("END", f"{end_dt.isoformat(timespec='seconds')} (status={status})")
        tr.raw(f"\nElapsed: {human_duration(elapsed)} ({elapsed:.1f}s)\n")
        tr.close()

        info: dict[str, Any] = {
            "question": question.title,
            "qid": question.qid,
            "answer_id": question.aid,
            "stem": stem,
            "status": status,
            "error": error_str,
            "model": cfg.model_friendly,
            "model_id": cfg.model_id,
            "model_arg": cfg.model_arg,
            "effort": cfg.effort,
            "config": cfg.config_label,
            "tools": {
                "python_execution": True,
                "web_search": cfg.web_search,
                "starsim_ai_plugin": cfg.plugin,
            },
            "context_1m": cfg.context_1m,
            "permission_mode": "bypassPermissions",
            "max_turns": cfg.max_turns,
            "max_budget_usd": cfg.max_budget_usd,
            "slug": cfg.slug,
            "start_time": start_dt.isoformat(timespec="seconds"),
            "end_time": end_dt.isoformat(timespec="seconds"),
            "elapsed_seconds": round(elapsed, 1),
            "elapsed_human": human_duration(elapsed),
            "is_error": is_error,
            "result_subtype": result_subtype,
            "num_turns": num_turns,
            "n_tool_uses": n_tool_uses,
            "tool_use_counts": tool_counts,
            "thinking_chars": thinking_chars,
            "answer_chars": len(answer_text),
            "duration_ms": duration_ms,
            "duration_api_ms": duration_api_ms,
            "session_id": session_id,
            "total_cost_usd": total_cost_usd,
            "usage_summary": summarize_usage(usage),
            "usage": yaml_safe(usage),
            "starsim_version": STARSIM_VERSION,
            "python_version": platform.python_version(),
            "answer_file": md_path.name,
            "log_file": log_path.name,
            "info_file": info_path.name,
            "workspace": str(workspace.relative_to(run_dir)),
            "init": yaml_safe(init_data),
        }
        info_path.write_text(
            yaml.safe_dump(info, sort_keys=False, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )

        prog.status = status
        prog.done = True

        cost_str = f"${total_cost_usd:.2f}" if total_cost_usd is not None else "n/a"
        toks = summarize_usage(usage).get("total_tokens", 0)
        print(
            f"  ■ {question.qid}: {status} in {human_duration(elapsed)} "
            f"| {toks:,} tok | {cost_str} | {n_tool_uses} tool calls "
            f"| {len(answer_text):,} chars → {md_path.name}",
            flush=True,
        )
        return info


# ---------------------------------------------------------------------------
# Batch driver
# ---------------------------------------------------------------------------


async def heartbeat(
    progress: dict[str, LiveProgress], interval: float, t0: float
) -> None:
    """Print a periodic one-block snapshot of every still-running agent."""
    try:
        while True:
            await asyncio.sleep(interval)
            running = [p for p in progress.values() if not p.done]
            if not running:
                continue
            n_done = sum(1 for p in progress.values() if p.done)
            lines = [
                f"  ─ heartbeat +{human_duration(time.perf_counter() - t0)} "
                f"({len(running)} running, {n_done} done) ─"
            ]
            for p in progress.values():
                if p.done:
                    continue
                if p.start_perf is None:
                    lines.append(f"      {p.qid}  queued")
                else:
                    elapsed = human_duration(time.perf_counter() - p.start_perf)
                    lines.append(
                        f"      {p.qid}  {elapsed:>8}  {p.n_tool_uses:>4} tool calls"
                        f"  last={(p.last_tool or '-'):<20}  {p.n_replies} replies"
                    )
            print("\n".join(lines), flush=True)
    except asyncio.CancelledError:
        pass


async def run_all(
    questions: list[QuestionSpec],
    cfg: RunConfig,
    max_concurrency: int,
    verbose: bool,
    heartbeat_interval: float,
) -> list[dict[str, Any]]:
    """Run all selected questions in parallel and return their metadata."""
    sem = asyncio.Semaphore(max_concurrency)
    progress = {q.qid: LiveProgress(qid=q.qid) for q in questions}
    t0 = time.perf_counter()
    tasks = [
        asyncio.create_task(run_question(q, cfg, sem, verbose, progress[q.qid]))
        for q in questions
    ]
    hb_task = (
        asyncio.create_task(heartbeat(progress, heartbeat_interval, t0))
        if heartbeat_interval and heartbeat_interval > 0
        else None
    )
    try:
        return await asyncio.gather(*tasks)
    finally:
        if hb_task is not None:
            hb_task.cancel()
            try:
                await hb_task
            except asyncio.CancelledError:
                pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run autonomous Claude Code agents to take the Starsim exam.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--model",
        default="sonnet",
        help="Model: friendly alias (haiku/sonnet/opus) or a full model id.",
    )
    p.add_argument(
        "--effort",
        default="medium",
        choices=VALID_EFFORTS,
        help="Reasoning effort / thinking budget.",
    )
    p.add_argument(
        "--config",
        default=None,
        help="Filename <config> tag. Default derived from the enabled tools "
        "(noskills / web / skills / full).",
    )
    p.add_argument(
        "--web-search",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Allow the WebSearch/WebFetch tools.",
    )
    p.add_argument(
        "--plugin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Load the starsim-ai plugin (Starsim skills + Context7 docs).",
    )
    p.add_argument(
        "--context-1m",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable the 1M-token context beta. Default: on for sonnet/opus, "
        "off for haiku.",
    )
    p.add_argument(
        "--questions",
        default="all",
        help="Comma-separated question ids to run (e.g. q01,q03) or 'all'.",
    )
    p.add_argument(
        "--questions-dir",
        type=Path,
        default=DEFAULT_QUESTIONS_DIR,
        help="Directory containing qNN_*.md question files.",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Base directory for answers (a <slug> subdir is created under it).",
    )
    p.add_argument(
        "--slug",
        default=None,
        help="Override the session slug (default: start time, e.g. jun13.0740).",
    )
    p.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Max agent loop iterations per question (default: unlimited).",
    )
    p.add_argument(
        "--max-budget-usd",
        type=float,
        default=None,
        help="Per-question USD budget safety cap (default: none).",
    )
    p.add_argument(
        "--max-concurrency",
        type=int,
        default=None,
        help="Max agents running at once (default: one per selected question).",
    )
    p.add_argument(
        "--heartbeat",
        type=float,
        default=30.0,
        help="Seconds between live progress heartbeats (0 to disable).",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Stream per-agent progress (assistant text and tool calls).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the run plan and exit without calling the model.",
    )
    return p.parse_args(argv)


def build_config(args: argparse.Namespace) -> tuple[RunConfig, list[QuestionSpec]]:
    """Validate args and assemble the RunConfig and question list."""
    instructions_file = args.questions_dir / INSTRUCTIONS_FILENAME
    if not instructions_file.exists():  # fall back to the canonical instructions
        instructions_file = DEFAULT_QUESTIONS_DIR / INSTRUCTIONS_FILENAME
    if not instructions_file.exists():
        raise FileNotFoundError(f"Missing exam instructions: {instructions_file}")
    instructions = instructions_file.read_text(encoding="utf-8")

    selected = [s.strip() for s in args.questions.split(",") if s.strip()]
    questions = discover_questions(args.questions_dir, selected)
    if not questions:
        raise ValueError("No questions selected.")

    friendly = friendly_model_name(args.model)
    model_id = MODEL_ALIASES.get(friendly, args.model)
    config_label = args.config or derive_config_label(args.web_search, args.plugin)

    context_1m = args.context_1m
    if context_1m is None:  # model-aware default
        context_1m = friendly != "haiku"

    cfg = RunConfig(
        model_friendly=friendly,
        model_arg=args.model,
        model_id=model_id,
        effort=args.effort,
        config_label=config_label,
        web_search=args.web_search,
        plugin=args.plugin,
        context_1m=context_1m,
        max_turns=args.max_turns,
        max_budget_usd=args.max_budget_usd,
        slug=args.slug or make_slug(),
        output_dir=args.output_dir,
        instructions=instructions,
    )
    return cfg, questions


def print_plan(cfg: RunConfig, questions: list[QuestionSpec], max_concurrency: int) -> None:
    run_dir = cfg.run_dir
    print("=" * 72)
    print("Starsim exam — taking agents")
    print("=" * 72)
    print(f"  slug:           {cfg.slug}")
    print(f"  model:          {cfg.model_friendly}  (sent as '{cfg.model_arg}', id {cfg.model_id})")
    print(f"  effort:         {cfg.effort}")
    print(f"  config label:   {cfg.config_label}")
    print(f"  web search:     {cfg.web_search}")
    print(f"  starsim plugin: {cfg.plugin}")
    print(f"  1M context:     {cfg.context_1m}")
    print(f"  max turns:      {cfg.max_turns if cfg.max_turns else 'unlimited'}")
    print(f"  max budget:     {('$%.2f' % cfg.max_budget_usd) if cfg.max_budget_usd else 'none'}")
    print(f"  concurrency:    {max_concurrency}")
    print(f"  starsim:        {STARSIM_VERSION}")
    print(f"  output dir:     {run_dir}")
    print("  questions:")
    for q in questions:
        print(f"    - {q.qid}: {q.title}  →  {q.aid}.md / .log / .info")
    print("=" * 72)


def write_manifest(
    cfg: RunConfig, questions: list[QuestionSpec], results: list[dict[str, Any]], elapsed: float
) -> Path:
    """Write a batch-level manifest.yaml summarizing the whole run."""
    run_dir = cfg.run_dir
    manifest = {
        "slug": cfg.slug,
        "created": datetime.now().isoformat(timespec="seconds"),
        "model": cfg.model_friendly,
        "model_id": cfg.model_id,
        "effort": cfg.effort,
        "config": cfg.config_label,
        "tools": {
            "python_execution": True,
            "web_search": cfg.web_search,
            "starsim_ai_plugin": cfg.plugin,
        },
        "context_1m": cfg.context_1m,
        "max_turns": cfg.max_turns,
        "max_budget_usd": cfg.max_budget_usd,
        "starsim_version": STARSIM_VERSION,
        "python_version": platform.python_version(),
        "total_elapsed_seconds": round(elapsed, 1),
        "total_elapsed_human": human_duration(elapsed),
        "total_cost_usd": round(
            sum((r.get("total_cost_usd") or 0.0) for r in results), 4
        ),
        "questions": [
            {
                "qid": r["qid"],
                "stem": r["stem"],
                "status": r["status"],
                "elapsed_human": r["elapsed_human"],
                "total_tokens": r.get("usage_summary", {}).get("total_tokens"),
                "total_cost_usd": r.get("total_cost_usd"),
                "answer_file": r["answer_file"],
            }
            for r in results
        ],
    }
    path = run_dir / "manifest.yaml"
    path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg, questions = build_config(args)
    max_concurrency = args.max_concurrency or len(questions)

    print_plan(cfg, questions, max_concurrency)

    if STARSIM_VERSION not in ("3.3", "unknown") and not STARSIM_VERSION.startswith("3.3"):
        print(
            f"  ⚠ Note: exam instructions reference Starsim v3.3, but v"
            f"{STARSIM_VERSION} is installed. Agents will use the installed version."
        )

    if args.dry_run:
        print("\nDry run — no agents launched.")
        return 0

    run_dir = cfg.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nLaunching {len(questions)} agent(s)…\n")
    t0 = time.perf_counter()
    results = asyncio.run(
        run_all(questions, cfg, max_concurrency, args.verbose, args.heartbeat)
    )
    elapsed = time.perf_counter() - t0

    manifest_path = write_manifest(cfg, questions, results, elapsed)

    print("\n" + "=" * 72)
    print(f"Done in {human_duration(elapsed)}. Results → {run_dir}")
    print(f"Manifest → {manifest_path}")
    print("=" * 72)
    total_cost = sum((r.get("total_cost_usd") or 0.0) for r in results)
    for r in results:
        toks = r.get("usage_summary", {}).get("total_tokens", 0) or 0
        cost = r.get("total_cost_usd")
        cost_str = f"${cost:.2f}" if cost is not None else "n/a"
        print(
            f"  {r['qid']}: {r['status']:<20} {r['elapsed_human']:>8} "
            f"| {toks:>10,} tok | {cost_str:>8} | {r['answer_file']}"
        )
    print(f"  TOTAL cost: ${total_cost:.2f}")

    # Exit non-zero if any agent failed outright.
    return 1 if any(r["status"] == "failed" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
