#!/bin/bash
# Run debug evaluation for prompt and agent architectures (in parallel via tmux)
#
# Each eval runs in its own tmux window. To watch progress:
#   tmux attach -t eval              # attach to the session
#   Ctrl-b n / Ctrl-b p              # next/previous window
#   Ctrl-b <window-number>           # jump to window 0-3
#   Ctrl-b d                         # detach (evals keep running)

SESSION="eval"
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DONE_DIR=$(mktemp -d)
START=$SECONDS

# Kill any existing session with the same name
tmux kill-session -t "$SESSION" 2>/dev/null

# Define evals: "window-name|inspect eval command..."
EVALS=(
    "prompt-gpt5mini|inspect eval eval/prompt/starsim.py --model openai/gpt-5-mini-2025-08-07 -T with_background=False -T with_test_cases=False -T tutorial=starsim_t1"
    "prompt-sonnet|inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 -T with_background=False -T with_test_cases=False -T tutorial=starsim_t1"
    "agent-sonnet|inspect eval eval/agent/starsim.py --model anthropic/claude-sonnet-4-6 -T model=sonnet -T with_plugin=False -T tutorial=starsim_t1"
    "agent-sonnet-plugin|inspect eval eval/agent/starsim.py --model anthropic/claude-sonnet-4-6 -T model=sonnet -T with_plugin=True -T tutorial=starsim_t1"
)

# Launch each eval in a tmux window
tmux new-session -d -s "$SESSION"
for entry in "${EVALS[@]}"; do
    name="${entry%%|*}"
    cmd="${entry#*|}"
    tmux new-window -t "$SESSION" -n "$name" \
        "cd '$REPO_ROOT' && $cmd; touch '$DONE_DIR/$name'; echo 'Done. Press enter to close.'; read"
done
tmux kill-window -t "$SESSION:0"  # remove the empty initial window

echo "Launched ${#EVALS[@]} evals in tmux session '$SESSION' and temp folder '$DONE_DIR':"
echo "  tmux attach -t $SESSION        # attach"
echo "  Ctrl-b n/p                     # switch windows"
echo "  Ctrl-b d                       # detach"
echo ""
echo "Waiting for all evals to finish..."

# Wait for all marker files
while [ "$(ls "$DONE_DIR" 2>/dev/null | wc -l)" -lt ${#EVALS[@]} ]; do
    sleep 5
done

rm -rf "$DONE_DIR"
elapsed=$(( SECONDS - START ))
echo ""
echo -e "\033[1;32mAll evaluations complete: $(( elapsed / 60 ))m $(( elapsed % 60 ))s\033[0m"
