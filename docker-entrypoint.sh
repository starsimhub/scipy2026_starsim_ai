#!/bin/bash
set -e

# Build CLI args from environment variables
args=(
    "--host" "${HOST:-0.0.0.0}"
    "--port" "${PORT:-9100}"
    "--workspace" "/home/agent/workspaces"
)

if [ -n "$MAX_TURNS" ]; then
    args+=("--max-turns" "$MAX_TURNS")
fi

if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "1" ]; then
    args+=("--verbose")
fi

if [ -n "$LOG_DIR" ]; then
    args+=("--log-dir" "$LOG_DIR")
fi

if [ -n "$RUN_ID" ]; then
    args+=("--run-id" "$RUN_ID")
fi

if [ -n "$PLUGIN_DIRS" ]; then
    IFS=',' read -ra DIRS <<< "$PLUGIN_DIRS"
    for dir in "${DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            echo "ERROR: Plugin directory '$dir' not found." >&2
            echo "Did you forget to initialize the git submodule? Run:" >&2
            echo "  git submodule init && git submodule update" >&2
            exit 1
        fi
        args+=("--plugin-dir" "$dir")
    done
fi

exec start-claude-code-server "${args[@]}"
