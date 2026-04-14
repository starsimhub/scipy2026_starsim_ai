# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).


## [Unreleased]

### Added
- Documentation audit and fixes (CONTRIBUTING.md, CHANGELOG.md, CODE_OF_CONDUCT.md, folder READMEs).

## [0.1.0] - 2026-03-05

Initial release for SciPy 2026 submission.

### Added
- Claude Code A2A server (`claude_a2a` package) exposing Claude Code as a discoverable agent.
- Evaluation harness with two modes:
  - **Prompt evaluation** (`eval/prompt/starsim.py`) — one-shot LLM benchmark via inspect-ai.
  - **Agent evaluation** (`eval/agent/starsim.py`) — iterative agent benchmark via A2A server.
- Evaluation dataset covering Starsim tutorials 1-6 (`problems/starsim_t*.md`), with Markdown-first workflow and JSONL generation.
- Streamlit problem browser (`problems/app.py`).
- Analysis scripts for post-evaluation performance plotting and token counting.
- Docker and Docker Compose configuration for containerized A2A servers.
- CI via GitHub Actions (pytest on push/PR to `main`).
