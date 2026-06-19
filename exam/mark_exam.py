"""
Exam-marking agent for the Starsim AI evaluation.

The companion to [`take_exam.py`](take_exam.py). Where the taker produces an
answer per question, the marker grades those answers **exactly against the
official marking scheme** and records a score with per-criterion rationale.

Given an answer run directory (``exam/answers/<slug>_<model>-<effort>-<config>/``
produced by ``take_exam.py``), this launches **one autonomous marking agent per
answer** (``answer01``–``answer04``) and runs them in parallel. Each marker is
handed, inline in its prompt:

  - the exam question (``questions/qNN_*.md``),
  - the official solution and marking scheme (``solutions/sNN_*.md``), and
  - the student's submitted answer (the top-level ``answerNN….md`` — the file
    the taker designates as graded).

The marker's working directory is the answer's scratch workspace
(``workspaces/answerNN…/``), so the figures the answer references resolve by
their relative paths and can be opened with ``Read``. The agent may also run the
student's code to verify claims, but it grades the submission as written and
awards only the marks the scheme defines.

For every answer (``answer01`` → ``marked01``) the marker writes three sibling
files into the **same run directory** as the answer:

  - ``markedNN….md``    — the student's full answer reproduced verbatim, with
                          the marking scheme (criteria checked off, a one-line
                          justification per criterion, and a subtotal) appended
                          at the bottom of each question, plus a grand total.
  - ``markedNN….log``   — the full transcript (thinking, tool calls, results).
  - ``markedNN….info``  — run metadata (YAML), including the awarded/possible
                          score.

A batch-level ``marking_manifest.yaml`` summarizes all questions: per-question
scores and the exam grand total and percentage.

Progress is followable live, exactly as with the taker: each marker's ``.log``
is written incrementally (``tail -f`` it), and a heartbeat prints a per-agent
snapshot every 30 s.

Examples:
    # Mark the most recent answer run with the default (sonnet) marker
    uv run python exam/mark_exam.py

    # Mark a specific run, using opus at high effort for stricter judgement
    uv run python exam/mark_exam.py --run jun13.0806_sonnet-medium-noskills \\
        --model opus --effort high

    # Mark only two answers, pointing at a non-default solutions folder
    uv run python exam/mark_exam.py --answers answer01,answer03 \\
        --solutions-dir /path/to/starsim_exam/solutions

    # Preview what would be marked without calling the model
    uv run python exam/mark_exam.py --dry-run

Run ``uv run python exam/mark_exam.py --help`` for all options.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import re
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

# Reuse the taker's helpers so the two runners stay in lock-step (transcript
# format, model aliases, usage accounting, the live heartbeat, …). Importing
# the module also clears the CLAUDECODE marker and records STARSIM_VERSION.
from take_exam import (
    EXAM_DIR,
    PROJECT_ROOT,
    DEFAULT_QUESTIONS_DIR,
    DEFAULT_OUTPUT_DIR,
    STARSIM_PLUGIN_DIR,
    WEB_TOOLS,
    MAX_TOOL_RESULT_CHARS,
    MODEL_ALIASES,
    VALID_EFFORTS,
    STARSIM_VERSION,
    Transcript,
    LiveProgress,
    heartbeat,
    yaml_safe,
    short_tool_name,
    stringify_tool_result,
    summarize_usage,
    human_duration,
    make_slug,
    friendly_model_name,
)

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

# The official solutions live in the sibling ``starsim_exam`` repo by default;
# override with --solutions-dir for any other layout.
DEFAULT_SOLUTIONS_DIR = PROJECT_ROOT.parent / "starsim_exam" / "solutions"

# Files the marker writes in its workspace; copied/parsed by the runner.
MARKED_FILENAME = "marked.md"
SCORE_FILENAME = "score.yaml"

# Section totals in a marking scheme look like ``## 1.2: Simple sims [32 marks]``
# (exactly two leading hashes; sub-question lines use five). Summing these gives
# the maximum marks for a question.
SECTION_MARKS_RE = re.compile(r"^##\s+.*?\[(\d+)\s*marks?\]", re.MULTILINE)

MARK_SYSTEM_PROMPT = (
    "You are an expert computational epidemiologist and an experienced, "
    "impartial examiner grading a practical exam on the Starsim disease-"
    "modeling library. You mark strictly and exactly according to the official "
    "marking scheme you are given: you award only the marks it defines, never "
    "invent new criteria, and never deduct for issues the scheme does not "
    "mention.\n\n"
    "You have a working Python environment in which Starsim is installed, and "
    "the student's saved figures are in your working directory. You may run the "
    "student's code and open their figures to verify their claims — but you are "
    "grading the answer as submitted, not rewriting it: award marks only for "
    "what the student actually did. Be fair, consistent, and rigorous, and "
    "justify every mark decision in one short sentence."
)

# Detailed marking rubric and output contract, embedded in the user prompt.
MARK_INSTRUCTIONS = """\
# Your task

Grade the student's submitted answer below **exactly against the official
marking scheme**, and record the result.

## How to mark

- The marking scheme lists criteria as checkbox items, each ending in a mark
  value, e.g. `- [ ] Correct specification of network: 2 marks`. For every
  criterion, decide whether the student's submission satisfies it and award the
  stated marks if so, or `0` if not.
- Honor the scheme's wording precisely:
  - Ranges and tolerances ("accept 105 - 115") — award if the student's value
    falls inside the range.
  - Alternatives ("also correct", "or a comparable approach") — accept any of
    the listed equivalent solutions.
  - Penalties ("0 marks if `sim.plot()` is used instead") — apply them.
  - "1 mark for each ..." style criteria — award per correct item, capped at the
    stated maximum.
- Most criteria are all-or-nothing: award the full listed value or 0. Only give
  a partial value when the criterion's wording explicitly allows it.
- The maximum for each question is the sum of its section totals (the `## …
  [N marks]` headers). Your awarded total must never exceed it.
- Grade the answer as written: code blocks are assumed to run top to bottom.
  You MAY execute the student's code or open their saved figures to confirm a
  claimed output, a plot, or a numerical value — do this whenever a criterion
  turns on correctness you cannot judge by reading alone.
- **Open every figure** the answer references (use `Read` on the PNG in your
  working directory) before scoring any plot-related criterion.
- If the answer is missing, truncated, or off-topic for a sub-part, award 0 for
  its criteria and say so.

## What to write

Write BOTH of the following files in your current working directory:

### 1. `marked.md` — the student's full answer, annotated with marks

This file must contain the student's complete answer with your marks appended
at the bottom of each question, so a reader can check your marking against what
the student actually wrote without opening a second file. Structure it as:

1. A title and a short summary: the grand total as `awarded / possible`, the
   percentage, and a per-section table (section id, title, awarded/possible).
2. For each sub-question, in order:
   a. Its id, title, and `[N marks]`.
   b. The student's answer for that sub-question, reproduced VERBATIM —
      including all prose, ```` ```python ```` code blocks, and figure
      references. Do NOT summarise, abridge, or rewrite the student's content.
      You may, however, add light inline MARKER annotations pointing out where
      the answer is right or wrong (see below).
   c. A `**Marks**` block at the BOTTOM of that sub-question: the scheme's
      criteria rewritten with the outcome filled in — `- [x]` if awarded,
      `- [ ]` if not — each annotated with the awarded mark and a one-sentence
      justification, e.g.:
      `- [x] Correct specification of network: **2/2** — uses ss.RandomNet(n_contacts=8).`
      Close the block with `**Subtotal: X/Y**`.
3. A closing line per section (`**Section 1.2 total: X/Y**`) and a final
   `**Grand total: X/Y (Z%)**`.

### Inline MARKER annotations

While reproducing the answer, annotate it inline to flag exactly where it is
correct or where it goes wrong — this is what makes the marking easy to check.
Keep annotations MINIMAL: a few targeted notes per sub-question, NOT a comment
on every line or paragraph.

- Inside ```` ```python ```` code blocks, add a comment on the relevant line,
  prefixed with `# MARKER:`. For example:
  `beta = 0.05  # MARKER: should be beta=0.8` or `# MARKER: correct vectorisation`.
- In prose, append an italic note at the end of the relevant sentence or
  paragraph, e.g. `*[MARKER: this explanation is incorrect — S is conserved]*`
  or `*[MARKER: correct]*`.

These are illustrative examples of the style and placement, not a prescriptive
format — annotate wherever it genuinely helps a reader see your reasoning.

Annotating the answer does not change the marks: grade the submission exactly
as written. The reproduction and annotations exist only so the marking can be
verified at a glance.

### 2. `score.yaml` — the machine-readable score

Use exactly this schema (ids and titles taken from the scheme's section
headers; `possible` values are the section totals; `total_*` are the sums):

```yaml
question: "01"
total_awarded: 58
total_possible: 64
sections:
  - id: "1.1"
    title: "What is Starsim?"
    awarded: 14
    possible: 14
  - id: "1.2"
    title: "Simple simulations"
    awarded: 27
    possible: 32
  - id: "1.3"
    title: "Exploring outputs"
    awarded: 17
    possible: 18
```

`total_possible` must equal the sum of the section `possible` values, and
`total_awarded` the sum of the section `awarded` values. Double-check the
arithmetic before you finish.
"""


# ---------------------------------------------------------------------------
# Configuration data
# ---------------------------------------------------------------------------


@dataclass
class MarkTask:
    """A single answer to be marked against its solution."""

    num: str  # e.g. "01"
    qid: str  # e.g. "q01"
    answer_stem: str  # e.g. "answer01"
    marker_stem: str  # e.g. "marked01"
    answer_path: Path  # the graded answer Markdown (top-level answerNN….md)
    question_path: Path  # questions/qNN_*.md
    solution_path: Path  # solutions/sNN_*.md
    workspace: Path  # the answer's scratch dir (figures live here)
    answer_status: str  # status recorded in the answer's .info, if any
    max_marks: int  # sum of section totals in the solution


@dataclass
class MarkConfig:
    """Shared configuration for a batch of marking agents."""

    run_dir: Path
    solutions_dir: Path
    questions_dir: Path
    model_friendly: str
    model_arg: str
    model_id: str
    effort: str
    web_search: bool
    plugin: bool
    context_1m: bool
    max_turns: int | None
    max_budget_usd: float | None
    slug: str  # marking session slug (distinct from the answer run's slug)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def resolve_run_dir(answers_dir: Path, run: str | None) -> Path:
    """Resolve the answer run directory to mark.

    Args:
        answers_dir: Base directory holding per-run subdirectories.
        run: A run-directory name, an absolute/relative path, or ``None`` to
            pick the most recently modified run under ``answers_dir``.

    Returns:
        The resolved run directory.
    """
    if run:
        candidate = Path(run)
        if candidate.is_dir():
            return candidate.resolve()
        candidate = answers_dir / run
        if candidate.is_dir():
            return candidate.resolve()
        raise FileNotFoundError(f"Run directory not found: {run}")

    subdirs = [d for d in answers_dir.iterdir() if d.is_dir()] if answers_dir.is_dir() else []
    if not subdirs:
        raise FileNotFoundError(
            f"No answer runs found under {answers_dir}; pass --run explicitly."
        )
    return max(subdirs, key=lambda d: d.stat().st_mtime).resolve()


def max_marks_from_solution(solution_text: str) -> int:
    """Sum the section totals (`## … [N marks]`) in a marking scheme."""
    return sum(int(m) for m in SECTION_MARKS_RE.findall(solution_text))


def _find_one(directory: Path, patterns: list[str]) -> Path | None:
    """Return the first file in ``directory`` matching any of ``patterns``."""
    for pat in patterns:
        matches = sorted(directory.glob(pat))
        if matches:
            return matches[0]
    return None


def discover_mark_tasks(cfg: MarkConfig, selected: list[str] | None) -> list[MarkTask]:
    """Find answers in the run directory and pair each with its solution.

    Answer files are the top-level ``answerNN….md`` in the run directory
    (excluding any previously written ``markedNN….md`` marked files). Each is
    matched to its question (``qNN_*.md``) and solution (``sNN_*.md``) by
    leading number.

    Args:
        cfg: The marking configuration (run/solutions/questions dirs).
        selected: Optional id filters (``answer01``/``q01``/``01``); ``None`` or
            ``"all"`` marks every answer found.

    Returns:
        A sorted list of [`MarkTask`][exam.mark_exam.MarkTask].
    """
    answer_files = sorted(
        f for f in cfg.run_dir.glob("answer*.md") if re.match(r"^answer\d", f.stem)
    )
    if not answer_files:
        raise FileNotFoundError(
            f"No answer files (answer*.md) found in {cfg.run_dir}. "
            "Point --run at a directory produced by take_exam.py."
        )

    wanted = None
    if selected and "all" not in selected:
        # Accept any of "answer01" / "a01" / "q01" / "01" by keeping the digits.
        wanted = {re.sub(r"\D", "", s) for s in selected}

    tasks: list[MarkTask] = []
    for af in answer_files:
        m = re.match(r"^answer(\d+)", af.stem)
        if not m:
            continue
        num = m.group(1)
        if wanted is not None and num not in wanted:
            continue

        question_path = _find_one(cfg.questions_dir, [f"q{num}_*.md", f"q{num}.md"])
        if question_path is None:
            print(f"  ⚠ skipping {af.name}: no question q{num}_*.md in {cfg.questions_dir}")
            continue
        solution_path = _find_one(cfg.solutions_dir, [f"s{num}_*.md", f"s{num}.md"])
        if solution_path is None:
            print(f"  ⚠ skipping {af.name}: no solution s{num}_*.md in {cfg.solutions_dir}")
            continue

        # Read the answer's status from its .info, if present (provenance only).
        answer_status = "unknown"
        info_path = cfg.run_dir / f"{af.stem}.info"
        if info_path.exists():
            try:
                answer_status = (yaml.safe_load(info_path.read_text()) or {}).get(
                    "status", "unknown"
                )
            except Exception:
                pass

        tasks.append(
            MarkTask(
                num=num,
                qid=f"q{num}",
                answer_stem=af.stem,
                marker_stem=f"marked{num}",
                answer_path=af,
                question_path=question_path,
                solution_path=solution_path,
                workspace=cfg.run_dir / "workspaces" / af.stem,
                answer_status=answer_status,
                max_marks=max_marks_from_solution(solution_path.read_text(encoding="utf-8")),
            )
        )

    if wanted is not None:
        found = {t.num for t in tasks}
        missing = wanted - found
        if missing:
            raise ValueError(
                f"Requested answers not found: {sorted(missing)}. "
                f"Available: {[t.num for t in tasks] or '(none)'}"
            )
    return tasks


# ---------------------------------------------------------------------------
# SDK options and prompt
# ---------------------------------------------------------------------------


def build_options(cfg: MarkConfig, workspace: Path) -> ClaudeAgentOptions:
    """Construct the ClaudeAgentOptions for one marking agent."""
    disallowed = [] if cfg.web_search else list(WEB_TOOLS)
    plugins = (
        [SdkPluginConfig(type="local", path=str(STARSIM_PLUGIN_DIR))]
        if cfg.plugin
        else []
    )

    opts = ClaudeAgentOptions(
        system_prompt=MARK_SYSTEM_PROMPT,
        permission_mode="bypassPermissions",
        cwd=str(workspace),
        model=cfg.model_arg,
        effort=cfg.effort,
        disallowed_tools=disallowed,
        plugins=plugins,
        env={"MPLBACKEND": "Agg"},
        setting_sources=None,
    )
    if cfg.max_turns:
        opts.max_turns = cfg.max_turns
    if cfg.max_budget_usd:
        opts.max_budget_usd = cfg.max_budget_usd
    if cfg.context_1m:
        opts.betas = ["context-1m-2025-08-07"]
    return opts


def build_prompt(cfg: MarkConfig, task: MarkTask) -> str:
    """Assemble the marker prompt: rubric + question + scheme + answer."""
    question_text = task.question_path.read_text(encoding="utf-8").strip()
    solution_text = task.solution_path.read_text(encoding="utf-8").strip()
    answer_text = task.answer_path.read_text(encoding="utf-8").strip()

    status_note = ""
    if task.answer_status not in ("completed", "unknown"):
        status_note = (
            f"\n> Note: this answer's run status was `{task.answer_status}` — it "
            "may be incomplete or a fallback capture. Mark whatever is present.\n"
        )

    figure_note = (
        "The student's saved figures are in your current working directory, "
        "referenced by their relative filenames in the answer above. Open each "
        "referenced figure with `Read` before scoring any plot-related "
        "criterion. You may also run the student's code to verify outputs."
    )

    return "\n".join(
        [
            MARK_INSTRUCTIONS.strip(),
            "",
            "---",
            "",
            "# The exam question (for reference)",
            "",
            question_text,
            "",
            "---",
            "",
            "# The official solution and marking scheme",
            "",
            solution_text,
            "",
            "---",
            "",
            f"# The student's submitted answer (this is what you are grading){status_note}",
            "",
            answer_text,
            "",
            "---",
            "",
            "# Figures and verification",
            "",
            figure_note,
            "",
        ]
    )


# ---------------------------------------------------------------------------
# Score parsing
# ---------------------------------------------------------------------------


def parse_score(workspace: Path) -> dict[str, Any] | None:
    """Read and lightly validate the marker's ``score.yaml``, if written."""
    score_path = workspace / SCORE_FILENAME
    if not (score_path.exists() and score_path.stat().st_size > 0):
        return None
    try:
        data = yaml.safe_load(score_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


# ---------------------------------------------------------------------------
# Per-answer marking run
# ---------------------------------------------------------------------------


async def run_marker(
    task: MarkTask,
    cfg: MarkConfig,
    sem: asyncio.Semaphore,
    verbose: bool,
    prog: LiveProgress,
) -> dict[str, Any]:
    """Run one marking agent on one answer and write its three files."""
    async with sem:
        run_dir = cfg.run_dir
        md_path = run_dir / f"{task.marker_stem}.md"
        log_path = run_dir / f"{task.marker_stem}.log"
        info_path = run_dir / f"{task.marker_stem}.info"

        # Mark inside the answer's scratch workspace so referenced figures
        # resolve by their relative paths. Fall back to a marking dir if the
        # workspace is missing (e.g. a no-answer run).
        workspace = task.workspace
        if not workspace.is_dir():
            workspace = run_dir / "marking" / task.marker_stem
        workspace.mkdir(parents=True, exist_ok=True)

        opts = build_options(cfg, workspace)
        prompt = build_prompt(cfg, task)

        tr = Transcript(log_path)
        tr.rule(f"MARKING TRANSCRIPT — {task.qid} ({task.answer_stem})")
        tr.raw(
            f"answer:      {task.answer_path.name}\n"
            f"question:    {task.question_path.name}\n"
            f"solution:    {task.solution_path.name}\n"
            f"max_marks:   {task.max_marks}\n"
            f"answer_stat: {task.answer_status}\n"
            f"model:       {cfg.model_friendly} ({cfg.model_id})\n"
            f"effort:      {cfg.effort}\n"
            f"web_search:  {cfg.web_search}\n"
            f"plugin:      {cfg.plugin}\n"
            f"workspace:   {workspace}\n"
        )

        start_dt = datetime.now()
        start_perf = time.perf_counter()
        prog.start_perf = start_perf
        prog.status = "running"
        tr.event("START", start_dt.isoformat(timespec="seconds"))
        print(f"  ▶ {task.qid}: marking → {run_dir.name}/{task.marker_stem}.md", flush=True)

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
                                    print(f"  · {task.qid}: {snippet}", flush=True)
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
                                print(f"  🔧 {task.qid}: {block.name}", flush=True)

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
        except Exception as exc:  # keep other markers alive
            status = "failed"
            error_str = f"{type(exc).__name__}: {exc}"
            tr.event("EXCEPTION", traceback.format_exc())
            print(f"  ✖ {task.qid}: FAILED — {error_str}", flush=True)

        # ----- resolve the marked answer -----
        ws_marked = workspace / MARKED_FILENAME
        marked_text = ""
        if ws_marked.exists() and ws_marked.stat().st_size > 0:
            marked_text = ws_marked.read_text(encoding="utf-8")
            md_path.write_text(marked_text, encoding="utf-8")
        else:
            fallback = (result_text or "\n".join(collected_text)).strip()
            if fallback:
                if status == "completed":
                    status = "no_marked_file"
                marked_text = fallback
                md_path.write_text(
                    "<!-- NOTE: the marker did not write marked.md; this is its "
                    "final message, captured as a fallback. -->\n\n"
                    + fallback
                    + "\n",
                    encoding="utf-8",
                )
            else:
                if status == "completed":
                    status = "no_marks"
                md_path.write_text(
                    "<!-- NOTE: the marker produced no output. -->\n", encoding="utf-8"
                )

        # ----- resolve the score -----
        score = parse_score(workspace)
        total_awarded: int | None = None
        total_possible: int | None = None
        percentage: float | None = None
        score_sections: Any = None
        if score is not None:
            total_awarded = score.get("total_awarded")
            total_possible = score.get("total_possible")
            score_sections = score.get("sections")
            if total_possible in (None, 0):
                total_possible = task.max_marks
            if isinstance(total_awarded, (int, float)) and total_possible:
                percentage = round(100.0 * total_awarded / total_possible, 1)
        elif status == "completed":
            status = "no_score_file"

        # ----- timing + metadata -----
        end_dt = datetime.now()
        elapsed = time.perf_counter() - start_perf
        tr.event("END", f"{end_dt.isoformat(timespec='seconds')} (status={status})")
        score_line = (
            f"{total_awarded}/{total_possible}" if total_awarded is not None else "n/a"
        )
        tr.raw(f"\nScore: {score_line}\nElapsed: {human_duration(elapsed)} ({elapsed:.1f}s)\n")
        tr.close()

        info: dict[str, Any] = {
            "qid": task.qid,
            "num": task.num,
            "answer_file": task.answer_path.name,
            "answer_stem": task.answer_stem,
            "answer_status": task.answer_status,
            "marker_stem": task.marker_stem,
            "question_file": task.question_path.name,
            "solution_file": task.solution_path.name,
            "status": status,
            "error": error_str,
            "total_awarded": total_awarded,
            "total_possible": total_possible,
            "max_marks_from_scheme": task.max_marks,
            "percentage": percentage,
            "sections": yaml_safe(score_sections) if score_sections is not None else None,
            "marker_model": cfg.model_friendly,
            "marker_model_id": cfg.model_id,
            "marker_model_arg": cfg.model_arg,
            "marker_effort": cfg.effort,
            "tools": {
                "python_execution": True,
                "web_search": cfg.web_search,
                "starsim_ai_plugin": cfg.plugin,
            },
            "context_1m": cfg.context_1m,
            "permission_mode": "bypassPermissions",
            "max_turns": cfg.max_turns,
            "max_budget_usd": cfg.max_budget_usd,
            "marking_slug": cfg.slug,
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
            "marked_chars": len(marked_text),
            "duration_ms": duration_ms,
            "duration_api_ms": duration_api_ms,
            "session_id": session_id,
            "total_cost_usd": total_cost_usd,
            "usage_summary": summarize_usage(usage),
            "usage": yaml_safe(usage),
            "starsim_version": STARSIM_VERSION,
            "python_version": platform.python_version(),
            "marked_file": md_path.name,
            "log_file": log_path.name,
            "info_file": info_path.name,
            "workspace": str(workspace.relative_to(run_dir)) if workspace.is_relative_to(run_dir) else str(workspace),
            "init": yaml_safe(init_data),
        }
        info_path.write_text(
            yaml.safe_dump(info, sort_keys=False, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )

        prog.status = status
        prog.done = True

        cost_str = f"${total_cost_usd:.2f}" if total_cost_usd is not None else "n/a"
        pct_str = f"{percentage}%" if percentage is not None else "n/a"
        print(
            f"  ■ {task.qid}: {status} | {score_line} ({pct_str}) "
            f"in {human_duration(elapsed)} | {cost_str} → {md_path.name}",
            flush=True,
        )
        return info


# ---------------------------------------------------------------------------
# Batch driver
# ---------------------------------------------------------------------------


async def run_all(
    tasks: list[MarkTask],
    cfg: MarkConfig,
    max_concurrency: int,
    verbose: bool,
    heartbeat_interval: float,
) -> list[dict[str, Any]]:
    """Run all marking tasks in parallel and return their metadata."""
    sem = asyncio.Semaphore(max_concurrency)
    progress = {t.qid: LiveProgress(qid=t.qid) for t in tasks}
    t0 = time.perf_counter()
    coros = [
        asyncio.create_task(run_marker(t, cfg, sem, verbose, progress[t.qid]))
        for t in tasks
    ]
    hb_task = (
        asyncio.create_task(heartbeat(progress, heartbeat_interval, t0))
        if heartbeat_interval and heartbeat_interval > 0
        else None
    )
    try:
        return await asyncio.gather(*coros)
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
        description="Run autonomous Claude Code agents to mark Starsim exam answers.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--run",
        default=None,
        help="Answer run to mark: a run-directory name (e.g. "
        "jun13.0806_sonnet-medium-noskills), a path, or omit for the most recent.",
    )
    p.add_argument(
        "--answers-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Base directory holding per-run answer subdirectories.",
    )
    p.add_argument(
        "--solutions-dir",
        type=Path,
        default=DEFAULT_SOLUTIONS_DIR,
        help="Directory containing sNN_*.md solutions / marking schemes.",
    )
    p.add_argument(
        "--questions-dir",
        type=Path,
        default=DEFAULT_QUESTIONS_DIR,
        help="Directory containing qNN_*.md question files.",
    )
    p.add_argument(
        "--answers",
        default="all",
        help="Comma-separated answer ids to mark (e.g. answer01,answer03 or q01,q03 or 01,03) or 'all'.",
    )
    p.add_argument(
        "--model",
        default="sonnet",
        help="Marker model: friendly alias (haiku/sonnet/opus) or a full model id.",
    )
    p.add_argument(
        "--effort",
        default="high",
        choices=VALID_EFFORTS,
        help="Reasoning effort / thinking budget for the marker.",
    )
    p.add_argument(
        "--web-search",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Allow the WebSearch/WebFetch tools while marking.",
    )
    p.add_argument(
        "--plugin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Load the starsim-ai plugin (skills + Context7 docs) while marking.",
    )
    p.add_argument(
        "--context-1m",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable the 1M-token context beta. Default: on for sonnet/opus, off for haiku.",
    )
    p.add_argument(
        "--slug",
        default=None,
        help="Override the marking session slug (default: start time, e.g. jun13.0740).",
    )
    p.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Max agent loop iterations per answer (default: unlimited).",
    )
    p.add_argument(
        "--max-budget-usd",
        type=float,
        default=None,
        help="Per-answer USD budget safety cap (default: none).",
    )
    p.add_argument(
        "--max-concurrency",
        type=int,
        default=None,
        help="Max markers running at once (default: one per answer).",
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
        help="Print the marking plan and exit without calling the model.",
    )
    return p.parse_args(argv)


def build_config(args: argparse.Namespace) -> tuple[MarkConfig, list[MarkTask]]:
    """Validate args and assemble the MarkConfig and task list."""
    run_dir = resolve_run_dir(args.answers_dir, args.run)
    if not args.solutions_dir.is_dir():
        raise FileNotFoundError(f"Solutions directory not found: {args.solutions_dir}")
    if not args.questions_dir.is_dir():
        raise FileNotFoundError(f"Questions directory not found: {args.questions_dir}")

    friendly = friendly_model_name(args.model)
    model_id = MODEL_ALIASES.get(friendly, args.model)

    context_1m = args.context_1m
    if context_1m is None:  # model-aware default
        context_1m = friendly != "haiku"

    cfg = MarkConfig(
        run_dir=run_dir,
        solutions_dir=args.solutions_dir.resolve(),
        questions_dir=args.questions_dir.resolve(),
        model_friendly=friendly,
        model_arg=args.model,
        model_id=model_id,
        effort=args.effort,
        web_search=args.web_search,
        plugin=args.plugin,
        context_1m=context_1m,
        max_turns=args.max_turns,
        max_budget_usd=args.max_budget_usd,
        slug=args.slug or make_slug(),
    )

    selected = [s.strip() for s in args.answers.split(",") if s.strip()]
    tasks = discover_mark_tasks(cfg, selected)
    if not tasks:
        raise ValueError("No answers selected for marking.")
    return cfg, tasks


def print_plan(cfg: MarkConfig, tasks: list[MarkTask], max_concurrency: int) -> None:
    print("=" * 72)
    print("Starsim exam — marking agents")
    print("=" * 72)
    print(f"  marking slug:   {cfg.slug}")
    print(f"  run marked:     {cfg.run_dir}")
    print(f"  solutions:      {cfg.solutions_dir}")
    print(f"  questions:      {cfg.questions_dir}")
    print(f"  marker model:   {cfg.model_friendly}  (sent as '{cfg.model_arg}', id {cfg.model_id})")
    print(f"  effort:         {cfg.effort}")
    print(f"  web search:     {cfg.web_search}")
    print(f"  starsim plugin: {cfg.plugin}")
    print(f"  1M context:     {cfg.context_1m}")
    print(f"  max turns:      {cfg.max_turns if cfg.max_turns else 'unlimited'}")
    print(f"  max budget:     {('$%.2f' % cfg.max_budget_usd) if cfg.max_budget_usd else 'none'}")
    print(f"  concurrency:    {max_concurrency}")
    print(f"  starsim:        {STARSIM_VERSION}")
    print("  answers to mark:")
    for t in tasks:
        print(
            f"    - {t.qid}: {t.answer_path.name}  vs  {t.solution_path.name} "
            f"(/{t.max_marks})  →  {t.marker_stem}.md"
        )
    print("=" * 72)


def write_manifest(
    cfg: MarkConfig, tasks: list[MarkTask], results: list[dict[str, Any]], elapsed: float
) -> Path:
    """Write a marking_manifest.yaml summarizing the whole marking batch."""
    run_dir = cfg.run_dir
    total_awarded = sum((r.get("total_awarded") or 0) for r in results)
    total_possible = sum(
        (r.get("total_possible") or r.get("max_marks_from_scheme") or 0) for r in results
    )
    overall_pct = round(100.0 * total_awarded / total_possible, 1) if total_possible else None

    manifest = {
        "marking_slug": cfg.slug,
        "created": datetime.now().isoformat(timespec="seconds"),
        "run_marked": run_dir.name,
        "solutions_dir": str(cfg.solutions_dir),
        "marker_model": cfg.model_friendly,
        "marker_model_id": cfg.model_id,
        "effort": cfg.effort,
        "tools": {
            "python_execution": True,
            "web_search": cfg.web_search,
            "starsim_ai_plugin": cfg.plugin,
        },
        "context_1m": cfg.context_1m,
        "starsim_version": STARSIM_VERSION,
        "python_version": platform.python_version(),
        "total_elapsed_seconds": round(elapsed, 1),
        "total_elapsed_human": human_duration(elapsed),
        "total_cost_usd": round(sum((r.get("total_cost_usd") or 0.0) for r in results), 4),
        "exam_total_awarded": total_awarded,
        "exam_total_possible": total_possible,
        "exam_percentage": overall_pct,
        "questions": [
            {
                "qid": r["qid"],
                "answer_file": r["answer_file"],
                "marked_file": r["marked_file"],
                "status": r["status"],
                "total_awarded": r.get("total_awarded"),
                "total_possible": r.get("total_possible") or r.get("max_marks_from_scheme"),
                "percentage": r.get("percentage"),
                "elapsed_human": r["elapsed_human"],
                "total_cost_usd": r.get("total_cost_usd"),
            }
            for r in results
        ],
    }
    path = run_dir / "marking_manifest.yaml"
    path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg, tasks = build_config(args)
    max_concurrency = args.max_concurrency or len(tasks)

    print_plan(cfg, tasks, max_concurrency)

    if args.dry_run:
        print("\nDry run — no markers launched.")
        return 0

    print(f"\nLaunching {len(tasks)} marking agent(s)…\n")
    t0 = time.perf_counter()
    results = asyncio.run(run_all(tasks, cfg, max_concurrency, args.verbose, args.heartbeat))
    elapsed = time.perf_counter() - t0

    manifest_path = write_manifest(cfg, tasks, results, elapsed)

    total_awarded = sum((r.get("total_awarded") or 0) for r in results)
    total_possible = sum(
        (r.get("total_possible") or r.get("max_marks_from_scheme") or 0) for r in results
    )
    overall_pct = round(100.0 * total_awarded / total_possible, 1) if total_possible else None

    print("\n" + "=" * 72)
    print(f"Done in {human_duration(elapsed)}. Marked → {cfg.run_dir}")
    print(f"Manifest → {manifest_path}")
    print("=" * 72)
    for r in results:
        aw = r.get("total_awarded")
        poss = r.get("total_possible") or r.get("max_marks_from_scheme")
        score_str = f"{aw}/{poss}" if aw is not None else "n/a"
        pct = r.get("percentage")
        pct_str = f"{pct}%" if pct is not None else "—"
        cost = r.get("total_cost_usd")
        cost_str = f"${cost:.2f}" if cost is not None else "n/a"
        print(
            f"  {r['qid']}: {r['status']:<18} {score_str:>10} {pct_str:>7} "
            f"| {r['elapsed_human']:>8} | {cost_str:>8} | {r['marked_file']}"
        )
    pct_str = f" ({overall_pct}%)" if overall_pct is not None else ""
    print(f"  EXAM TOTAL: {total_awarded}/{total_possible}{pct_str}")
    total_cost = sum((r.get("total_cost_usd") or 0.0) for r in results)
    print(f"  TOTAL cost: ${total_cost:.2f}")

    return 1 if any(r["status"] == "failed" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
