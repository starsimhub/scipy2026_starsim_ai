# Agentic evaluation

Tests the performance of Claude models ith different configurations (with/without plugins) using an agent-to-agent (A2A) architecture. Agents are tasked with writing, testing, and debugging Starsim code.

## Files

- **`run.sh`** — Runs the Claude models against both A2A server configurations (with and without the Starsim plugin). Requires `docker compose up` first.
- **`starsim.py`** — The `inspect-ai` evaluation task. Sends each problem to an A2A server, where the agent can write code, run tests, and iterate. Scores the final solution against test cases.


## Usage

```bash
# Start the A2A servers
docker compose up --build

# Run evaluations
./eval/agent/run.sh

# Run a single evaluation
inspect eval eval/agent/starsim.py -T model=sonnet

# Check plugin configuration
python eval/agent/check_plugin.py
```
