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

# Create session with first eval
tmux new-session -d -s "$SESSION" -n "prompt-gpt5mini" \
    "cd '$REPO_ROOT' && inspect eval eval/prompt/starsim.py --model openai/gpt-5-mini-2025-08-07 -T with_background=False -T with_test_cases=False -T tutorial=starsim_t1; touch '$DONE_DIR/prompt-gpt5mini'; echo 'Done. Press enter to close.'; read"

tmux new-window -t "$SESSION" -n "prompt-sonnet" \
    "cd '$REPO_ROOT' && inspect eval eval/prompt/starsim.py --model anthropic/claude-sonnet-4-6 -T with_background=False -T with_test_cases=False -T tutorial=starsim_t1; touch '$DONE_DIR/prompt-sonnet'; echo 'Done. Press enter to close.'; read"

tmux new-window -t "$SESSION" -n "agent-sonnet" \
    "cd '$REPO_ROOT' && inspect eval eval/agent/starsim.py --model anthropic/claude-sonnet-4-6 -T model=sonnet -T with_plugin=False -T tutorial=starsim_t1; touch '$DONE_DIR/agent-sonnet'; echo 'Done. Press enter to close.'; read"

tmux new-window -t "$SESSION" -n "agent-sonnet-plugin" \
    "cd '$REPO_ROOT' && inspect eval eval/agent/starsim.py --model anthropic/claude-sonnet-4-6 -T model=sonnet -T with_plugin=True -T tutorial=starsim_t1; touch '$DONE_DIR/agent-sonnet-plugin'; echo 'Done. Press enter to close.'; read"

echo "Launched 4 evals in tmux session '$SESSION'"
echo "  tmux attach -t $SESSION        # attach"
echo "  Ctrl-b n/p                     # switch windows"
echo "  Ctrl-b d                       # detach"
echo ""
echo "Waiting for all evals to finish..."

# Wait for all 4 marker files
while [ "$(ls "$DONE_DIR" 2>/dev/null | wc -l)" -lt 4 ]; do
    sleep 5
done

rm -rf "$DONE_DIR"
elapsed=$(( SECONDS - START ))
echo ""
echo -e "\033[1;32mAll evaluations complete: $(( elapsed / 60 ))m $(( elapsed % 60 ))s\033[0m"
