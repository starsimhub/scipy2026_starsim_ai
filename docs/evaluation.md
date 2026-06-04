# Evaluation dataset

Our evaluation benchmark follows the structure of
[SciCode](https://arxiv.org/abs/2407.13168), adapted for disease modeling with
[Starsim](https://github.com/starsimhub/starsim). A central goal of this
benchmark is to measure how well an agent can **leverage Starsim as a library**
to solve modeling problems, rather than writing disease models from scratch.
Agents that effectively use Starsim's built-in components (e.g., `ss.SIR`,
`ss.Vaccine`, contact networks) demonstrate the kind of library fluency that
matters in practice. Furthermore, we add a time limit on the agent evaluation to
assess the time required to find a solution (or not!).

To assess this, we depart from SciCode in one key way: in addition to test-case
validation, we use an **LLM-judge assessment** to evaluate whether the agent's
solution actually uses Starsim APIs. This catches cases where an agent produces
numerically correct output but bypasses Starsim entirely (e.g., by implementing
ODE solvers from scratch). The judge reviews the generated code and scores it on
Starsim API usage, idiomatic patterns, and appropriate use of library
abstractions.

## Browse the evaluation dataset

A Streamlit app lets you browse the evaluation problems interactively:

```bash
uv run streamlit run problems/app.py
```

## Problem structure

Each problem is a multi-step disease modeling task. The **source of truth** is a
set of human-readable Markdown files (`problems/starsim_t*.md`). These are
converted to JSONL (`problems/starsim_t*.jsonl`) for consumption by the
evaluation harness.

**Editing problems:** Edit the `.md` files, then regenerate the JSONL:

```bash
python3 problems/build_jsonl.py
```

A test (`test_jsonl_matches_markdown`) ensures the JSONL files stay in sync with
the Markdown sources — if you edit a `.md` file without regenerating,
`uv run pytest tests/test_problems.py` will fail.

Problems are organized hierarchically:

**Main Problem** — A complete modeling task (e.g., "Build an SIR model with
age-stratified mixing and calibrate to observed data").

Each main problem decomposes into sequential **subproblems**, where later steps
can depend on outputs from earlier ones.

### Fields per subproblem

| Field | Description |
|---|---|
| `problem_id` | Unique identifier for the main problem (e.g., `"starsim_01"`) |
| `sub_step_id` | Identifier for the subproblem (e.g., `"starsim_01.3"`) |
| `description` | Natural language description of the task |
| `function_header` | Python function signature to implement |
| `docstring` | Input/output specification |
| `background` | Optional domain context (epidemiology concepts, model equations, parameter definitions) |
| `dependencies` | Allowed Python packages (e.g., `starsim`, `numpy`, `scipy`, `matplotlib`) |
| `test_cases` | Input-output pairs and domain-specific validations |
| `gold_solution` | Reference implementation |

### Example problem outline

```text
Problem: starsim_01 — "SIR model with vaccination campaign"
  ├── Sub 1: Define disease parameters and create an SIR model
  ├── Sub 2: Add age-stratified contact network
  ├── Sub 3: Implement a time-varying vaccination intervention
  ├── Sub 4: Run the simulation and extract results
  └── Sub 5: Plot epidemic curves and compute final size
```

## Evaluation modes

Following SciCode, we support multiple evaluation configurations:

| Mode | Background provided? | Prior solutions | Tests |
|---|---|---|---|
| **Standard** | No | Model-generated | Measures real-world capability |
| **With background** | Yes | Model-generated | Measures instruction-following |
| **Gold prior** | No | Gold solutions | Isolates per-step capability |
| **With background + gold prior** | Yes | Gold solutions | Easiest setting |

## Evaluation criteria

Each solution is assessed on two axes:

1. **Correctness** — Does the solution pass the test cases? (Same as SciCode.)
2. **Starsim utilization** — Does the solution use Starsim effectively? An LLM
   judge reviews the generated code and scores it on:
   - Whether core Starsim APIs are used (e.g., `ss.Sim`, `ss.SIR`, `ss.Network`)
   - Whether library abstractions are used appropriately (e.g., using
     `ss.Vaccine` instead of manually modifying susceptibility)
   - Whether the code follows idiomatic Starsim patterns

A solution that passes all test cases but doesn't use Starsim would score high on
correctness but low on utilization. The benchmark is designed to reward agents
that can learn and apply a domain library, not just produce correct numerical
output.

## Problem domains

Problems span core Starsim use cases:

- **Basic modeling** — SIR/SIS/SEIR dynamics, parameter configuration
- **Demographics** — Birth/death processes, age structure, population networks
- **Interventions** — Vaccination campaigns, treatment protocols, behavioral changes
- **Calibration** — Fitting models to observed data, likelihood-based calibration
- **Analysis** — Result extraction, plotting, sensitivity analysis
- **Multi-disease** — Co-circulating pathogens, disease interactions
- **Advanced networks** — Household structure, spatial mixing, dynamic contact patterns
