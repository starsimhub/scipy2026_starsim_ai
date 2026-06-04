# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `CHANGELOG.md` to track notable changes going forward.
- `docs/` documentation site built with MkDocs + Material, including a
  Getting Started tutorial, architecture and evaluation explanations, an
  execution-logging reference, and an auto-generated API reference
  (mkdocstrings). Published to GitHub Pages via `.github/workflows/docs.yml`.
- Usage examples and cross-references in the docstrings of key public objects
  (`ClaudeCodeConfig`, `ClaudeCodeExecutor`, `load_problems`, `run_tests`, and
  the `@task` benchmark functions).

### Changed
- Restructured `README.md`: the landing section now explains why evaluating AI
  agents on Starsim matters, and the long Architecture, Evaluation dataset, and
  Execution logging sections moved to dedicated pages under `docs/`.

### Fixed
- Typo in `eval/agent/README.md` ("ith" → "with").

## [0.1.0] - 2026-02-25

### Added
- Claude Code **A2A server** (`claude_a2a/`) exposing Claude Code as a
  discoverable, callable coding agent over HTTP, with workspace isolation,
  multi-turn sessions, streaming progress, cancellation, configurable tools,
  MCP extensibility, plugin support, and structured JSONL execution logging.
- **Prompt evaluation** (`eval/prompt/`): one-shot `inspect-ai` benchmark
  scoring a model's Starsim code against test cases.
- **Agent evaluation** (`eval/agent/`): iterative `inspect-ai` benchmark that
  sends problems to the A2A server so the agent can write, test, and debug code.
- **Evaluation dataset** (`problems/`): six tutorial problem sets
  (introduction, model building, demographics, diseases, networks,
  interventions), authored as Markdown and compiled to JSONL via
  `build_jsonl.py`, plus a Streamlit browser (`app.py`).
- **Analysis scripts** (`analysis/`) for plotting results and extracting
  statistics for the paper.
- **Docker Compose** services for the four server configurations
  (sonnet / opus × with / without the Starsim plugin).
- GitHub Actions CI running `pytest -m "not uses_llm"`.
- Project documentation: `README.md`, `CONTRIBUTING.md`, `LICENSE` (MIT), and
  folder-level READMEs.

[Unreleased]: https://github.com/starsimhub/scipy2026_starsim_ai/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/starsimhub/scipy2026_starsim_ai/releases/tag/v0.1.0
