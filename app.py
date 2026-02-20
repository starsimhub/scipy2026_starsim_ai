"""Streamlit app to browse the Starsim AI evaluation dataset."""

import json
from pathlib import Path

import streamlit as st

PROBLEMS_DIR = Path(__file__).parent / "problems"

PROBLEM_LABELS = {
    "starsim_t1": "Tutorial 1 — Introduction (Basic SIR/SIS Dynamics)",
    "starsim_t2": "Tutorial 2 — Building Your Model (Components & Parameters)",
    "starsim_t3": "Tutorial 3 — Demographics (Births, Deaths & Projections)",
}


@st.cache_data
def load_problems() -> list[dict]:
    """Load all problems from JSONL files."""
    problems = []
    for path in sorted(PROBLEMS_DIR.glob("*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                problems.append(json.loads(line))
    return problems


def main():
    st.set_page_config(page_title="Starsim Eval Browser", layout="wide")
    st.title("Starsim AI Evaluation Dataset")

    problems = load_problems()

    # Group by problem_id
    grouped: dict[str, list[dict]] = {}
    for p in problems:
        grouped.setdefault(p["problem_id"], []).append(p)

    # Sidebar — select main problem
    problem_ids = list(grouped.keys())
    selected_id = st.sidebar.selectbox(
        "Main Problem",
        problem_ids,
        format_func=lambda pid: PROBLEM_LABELS.get(pid, pid),
    )

    sub_problems = grouped[selected_id]

    # Sidebar — select sub-step
    selected_sub = st.sidebar.selectbox(
        "Sub-step",
        sub_problems,
        format_func=lambda p: f"{p['sub_step_id']}: {p['description'][:60]}…",
    )

    show_solution = st.sidebar.checkbox("Show gold solution", value=False)

    # Main content
    st.header(PROBLEM_LABELS.get(selected_id, selected_id))
    st.subheader(selected_sub["sub_step_id"])

    st.markdown("### Description")
    st.markdown(selected_sub["description"])

    if selected_sub.get("background"):
        st.markdown("### Background")
        st.markdown(selected_sub["background"])

    st.markdown("### Function Header")
    st.code(selected_sub["function_header"], language="python")

    st.markdown("### Docstring")
    st.code(selected_sub["docstring"], language="text")

    st.markdown("### Dependencies")
    st.write(", ".join(f"`{d}`" for d in selected_sub["dependencies"]))

    st.markdown("### Test Cases")
    for i, tc in enumerate(selected_sub["test_cases"], 1):
        with st.expander(f"Test {i}: {tc['description']}"):
            st.code(tc["test"], language="python")

    if show_solution:
        st.markdown("### Gold Solution")
        st.code(selected_sub["gold_solution"], language="python")


if __name__ == "__main__":
    main()
