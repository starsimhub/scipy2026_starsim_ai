# Agentic evaluation

Tests the performance of different models (e.g. Claude, GPT) with different configurations (with/without plugins) using an agent-to-agent (A2A) architecture. Agents are tasked with writing, testing, and debugging Starsim code.

## Files

- **`run.sh`** — Runs the full evaluation matrix: multiple models (Claude, GPT) against both A2A server configurations (with and without the Starsim plugin). Requires `docker compose up` first.
- **`starsim.py`** — The `inspect-ai` evaluation task. Sends each problem to an A2A server, where the agent can write code, run tests, and iterate. Scores the final solution against test cases.
- **`check_plugin.py`** — Smoke test that verifies the two Docker A2A servers are configured correctly: one with the Starsim plugin and one without.


## Usage

```bash
# Start the A2A servers
docker compose up --build

# Run all evaluations
./eval/agent/run.sh

# Run a single evaluation
inspect eval eval/agent/starsim.py -T agent_url=http://localhost:9100

# Check plugin configuration
python eval/agent/check_plugin.py
```
