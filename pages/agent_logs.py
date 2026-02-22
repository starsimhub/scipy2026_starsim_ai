"""Streamlit page to browse and analyze agent execution logs."""

import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

AGENT_LOGS_DIR = Path(__file__).parent.parent / "agent_logs"


@st.cache_data
def load_all_logs() -> dict[str, list[dict]]:
    """Load all JSONL log files, grouped by run directory (or 'default').

    Returns a dict: run_id -> list of {task_id, events, file_path}.
    """
    runs: dict[str, list[dict]] = {}

    if not AGENT_LOGS_DIR.exists():
        return runs

    # Support both flat layout (agent_logs/*.jsonl) and nested (agent_logs/<run_id>/*.jsonl)
    jsonl_files = list(AGENT_LOGS_DIR.glob("*.jsonl"))
    nested_files = list(AGENT_LOGS_DIR.glob("*/*.jsonl"))

    # Flat files go under "default" run
    for path in sorted(jsonl_files):
        events = _parse_jsonl(path)
        run_id = _detect_run_id(events) or "default"
        runs.setdefault(run_id, []).append(
            {"task_id": path.stem, "events": events, "file_path": str(path)}
        )

    # Nested files use parent dir name as run_id
    for path in sorted(nested_files):
        events = _parse_jsonl(path)
        run_id = path.parent.name
        runs.setdefault(run_id, []).append(
            {"task_id": path.stem, "events": events, "file_path": str(path)}
        )

    return runs


def _parse_jsonl(path: Path) -> list[dict]:
    events = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _detect_run_id(events: list[dict]) -> str | None:
    """Try to extract run_id from log events."""
    for e in events:
        if "run_id" in e:
            return e["run_id"]
    return None


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def summarize_task(events: list[dict]) -> dict:
    """Compute summary statistics from a task's event log."""
    summary: dict = {}

    # Task description from the prompt
    for e in events:
        if e["event"] == "task_start":
            prompt = e.get("prompt", "")
            # Extract function name from prompt if present
            for line in prompt.splitlines():
                if line.strip().startswith("def "):
                    summary["function"] = line.strip().split("(")[0].replace("def ", "")
                    break
            # Extract short description (first non-empty line of problem description)
            in_desc = False
            for line in prompt.splitlines():
                if "## Problem Description" in line:
                    in_desc = True
                    continue
                if in_desc and line.strip() and not line.startswith("##"):
                    summary["description"] = line.strip()
                    break
            summary["model"] = e.get("model", "unknown")
            summary["workspace"] = e.get("workspace", "")
            break

    # Tool call counts
    tool_calls = [e for e in events if e["event"] == "tool_use"]
    summary["tool_call_count"] = len(tool_calls)

    tool_names: dict[str, int] = {}
    for tc in tool_calls:
        name = tc.get("tool", "unknown")
        tool_names[name] = tool_names.get(name, 0) + 1
    summary["tool_breakdown"] = tool_names

    # Timing
    timestamps = [e["ts"] for e in events if "ts" in e]
    if len(timestamps) >= 2:
        duration = timestamps[-1] - timestamps[0]
        summary["duration_seconds"] = round(duration, 1)
        summary["start_time"] = _format_ts(timestamps[0])
        summary["end_time"] = _format_ts(timestamps[-1])
    else:
        summary["duration_seconds"] = 0

    # Outcome
    has_error = any(e["event"] == "error" for e in events)
    has_complete = any(e["event"] == "task_complete" for e in events)
    if has_error and not has_complete:
        summary["status"] = "error"
    elif has_complete:
        summary["status"] = "completed"
    else:
        summary["status"] = "unknown"

    # Response length
    for e in events:
        if e["event"] == "task_complete" and "response_len" in e:
            summary["response_len"] = e["response_len"]

    # Count assistant messages
    assistant_texts = [e for e in events if e["event"] == "assistant_text"]
    summary["assistant_message_count"] = len(assistant_texts)

    return summary


def _format_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

_EVENT_ICONS = {
    "task_start": "🚀",
    "tool_use": "🔧",
    "assistant_text": "💬",
    "result": "📋",
    "task_complete": "✅",
    "error": "❌",
}


def render_event(event: dict) -> None:
    """Render a single log event in a human-readable way."""
    ev_type = event.get("event", "unknown")
    icon = _EVENT_ICONS.get(ev_type, "📌")
    ts = _format_ts(event["ts"]) if "ts" in event else ""

    if ev_type == "task_start":
        st.markdown(f"**{icon} Task Started** — {ts}")
        model = event.get("model", "unknown")
        st.markdown(f"**Model:** `{model}`")
        if event.get("workspace"):
            st.markdown(f"**Workspace:** `{event['workspace']}`")
        with st.expander("Full Prompt", expanded=False):
            st.markdown(event.get("prompt", "_no prompt_"))

    elif ev_type == "tool_use":
        tool = event.get("tool", "unknown")
        st.markdown(f"**{icon} Tool Call:** `{tool}` — {ts}")
        inp = event.get("input", "")
        if isinstance(inp, str) and inp.startswith("{"):
            try:
                parsed = json.loads(inp)
                # Show a short summary for Bash commands
                if tool == "Bash" and "command" in parsed:
                    st.code(parsed["command"], language="bash")
                elif tool == "Task" and "prompt" in parsed:
                    desc = parsed.get("description", "")
                    st.markdown(f"*{desc}*")
                    with st.expander("Task prompt", expanded=False):
                        st.text(parsed["prompt"][:2000])
                else:
                    with st.expander("Input", expanded=False):
                        st.json(parsed)
            except json.JSONDecodeError:
                with st.expander("Input", expanded=False):
                    st.text(inp[:2000])
        elif inp:
            with st.expander("Input", expanded=False):
                st.text(str(inp)[:2000])

    elif ev_type == "assistant_text":
        st.markdown(f"**{icon} Assistant** — {ts}")
        st.markdown(event.get("text", ""))

    elif ev_type == "result":
        session = event.get("session_id", "unknown")
        st.markdown(f"**{icon} Result** — session `{session[:12]}...` — {ts}")

    elif ev_type == "task_complete":
        resp_len = event.get("response_len", "?")
        st.markdown(f"**{icon} Task Complete** — response length: {resp_len} chars — {ts}")

    elif ev_type == "error":
        st.error(f"**{icon} Error** — {ts}\n\n{event.get('error', 'unknown error')}")

    else:
        st.markdown(f"**{icon} {ev_type}** — {ts}")
        with st.expander("Raw event"):
            st.json(event)


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Agent Logs Viewer", layout="wide", page_icon="📊")
    st.title("📊 Agent Execution Logs")

    runs = load_all_logs()

    if not runs:
        st.warning("No agent logs found. Run an evaluation to generate logs.")
        return

    # ---- Sidebar: select run ----
    run_ids = sorted(runs.keys())
    selected_run = st.sidebar.selectbox(
        "Evaluation Run",
        run_ids,
        format_func=lambda r: f"Run: {r}" if r != "default" else "Default (flat logs)",
    )

    tasks = runs[selected_run]

    # Build labels for task selector
    task_labels: dict[str, str] = {}
    task_summaries: dict[str, dict] = {}
    for t in tasks:
        s = summarize_task(t["events"])
        task_summaries[t["task_id"]] = s
        func = s.get("function", "")
        desc = s.get("description", "")
        label = func or desc or t["task_id"]
        dur = s.get("duration_seconds", 0)
        status_icon = {"completed": "✅", "error": "❌"}.get(s.get("status", ""), "⏳")
        task_labels[t["task_id"]] = f"{status_icon} {label} ({dur}s)"

    selected_task_id = st.sidebar.selectbox(
        "Task",
        [t["task_id"] for t in tasks],
        format_func=lambda tid: task_labels.get(tid, tid),
    )

    # ---- Run-level summary ----
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Tasks in run:** {len(tasks)}")
    total_tools = sum(s["tool_call_count"] for s in task_summaries.values())
    total_time = sum(s["duration_seconds"] for s in task_summaries.values())
    completed = sum(1 for s in task_summaries.values() if s.get("status") == "completed")
    errored = sum(1 for s in task_summaries.values() if s.get("status") == "error")
    st.sidebar.markdown(f"**Completed:** {completed} | **Errors:** {errored}")
    st.sidebar.markdown(f"**Total tool calls:** {total_tools}")
    st.sidebar.markdown(f"**Total time:** {total_time:.0f}s")

    # Find selected task
    selected_task = next(t for t in tasks if t["task_id"] == selected_task_id)
    summary = task_summaries[selected_task_id]

    # ---- Summary section ----
    st.header("Task Summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", summary.get("status", "unknown").title())
    col2.metric("Duration", f"{summary.get('duration_seconds', 0)}s")
    col3.metric("Tool Calls", summary.get("tool_call_count", 0))
    col4.metric("Assistant Messages", summary.get("assistant_message_count", 0))

    col5, col6, col7 = st.columns(3)
    col5.metric("Model", summary.get("model", "unknown"))
    col6.metric("Response Length", f"{summary.get('response_len', '?')} chars")
    col7.metric("Start Time", summary.get("start_time", "?"))

    # Tool breakdown
    if summary.get("tool_breakdown"):
        st.subheader("Tool Usage Breakdown")
        breakdown = summary["tool_breakdown"]
        cols = st.columns(min(len(breakdown), 6))
        for i, (tool, count) in enumerate(sorted(breakdown.items(), key=lambda x: -x[1])):
            cols[i % len(cols)].metric(tool, count)

    # ---- Event timeline ----
    st.header("Event Timeline")

    # Filter options
    event_types = sorted({e["event"] for e in selected_task["events"]})
    selected_types = st.multiselect(
        "Filter by event type",
        event_types,
        default=event_types,
    )

    filtered_events = [e for e in selected_task["events"] if e["event"] in selected_types]

    for event in filtered_events:
        st.divider()
        render_event(event)

    # ---- Raw JSON ----
    with st.expander("Raw JSONL data"):
        st.json(selected_task["events"])


if __name__ == "__main__":
    main()
