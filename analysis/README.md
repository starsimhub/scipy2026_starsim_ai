# Analysis

Post-evaluation analysis scripts for plotting results and extracting statistics for the paper.

## Scripts

- **`eval_performance.py`** — Main results visualization: loads inspect-ai eval logs and generates performance plots with seaborn.
- **`quantify_results.py`** — Extracts numeric results (pass rates, scores) for the abstract and paper text.
- **`calculate_tokens.py`** — Computes token usage ratios between models and plugin/no-plugin configurations.
- **`debug_evals.py`** — Prints detailed debugging information from eval log files.

## Usage

These scripts expect eval logs in `../logs/`. Run from this directory:

```bash
python eval_performance.py
python quantify_results.py
```

## Dependencies

Additional dependencies beyond the main project are listed in `requirements.txt`.
