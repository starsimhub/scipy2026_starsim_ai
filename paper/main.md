---
# Ensure that this title is the same as the one in `myst.yml`
title: "Vibes, meet rigor: Evaluating and improving AI performance on complex scientific code"
abstract: |
  Scientists apply rigorous methods to their research, but rarely to the AI tools they use to write code. We tested different LLM models in combination with domain-specific tools (including MCP servers and skills) to find the optimal combination for writing complex domain-specific code. We created a quantitative proficiency test for Starsim, a disease modeling framework, and evaluated different combinations of models and tools. While Claude Opus outperformed other models, access to tools allowed cheaper models (like Haiku) to perform almost as well as more expensive ones. Thus, to improve LLM performance on domain-specific problems, we recommend developing a set of tools with the help of quantitative evaluation.
---

## Introduction

Scientists are often decidedly unscientific about choosing AI tools to help them write code. They know these tools are helpful, but except for trying out different models, they rarely perform controlled evaluations to check whether other changes to their AI workflow produce significantly better results. This is because writing and executing these evaluations is typically time-consuming, the results of the evaluations are difficult to interpret and quantify, and AI workflows and tooling are evolving rapidly. Here we describe our process for quantitatively testing our assumptions about how to build a good AI assistant.

A growing number of benchmarks evaluate the coding ability of LLMs and agents, ranging from resolving real-world software-engineering issues (SWE-bench [@swebench]) to completing open-ended tasks in a terminal environment (Terminal-Bench [@terminalbench]) and implementing routines for scientific computing (SciCode [@scicode]). These benchmarks have driven rapid progress, but they largely target widely-used, general-purpose libraries that are well represented in model training data. They say little about how well agents handle specialized scientific software — code that is comparatively rare in training corpora, evolves quickly, and demands domain expertise to use correctly. This is precisely the regime in which most research software lives, and the one we set out to measure.

## Methods

### Starsim

Our team models infectious diseases using [Starsim](https://starsim.org/) [@starsim], a high-performance agent-based modeling library built on NumPy [@numpy], SciPy [@scipy], and Numba. A Starsim model is assembled from composable modules — diseases, contact networks, interventions, demographics, connectors, and analyzers — that plug into a central `Sim` object operating on a shared `People` population. Agents are represented as structured arrays rather than Python objects, and performance-critical inner loops are accelerated with Numba, allowing simulations of millions of agents. Starsim also provides first-class abstractions that are easy to get subtly wrong, including a unit-aware time system (rates, probabilities, and durations), common-random-number machinery for variance reduction across scenarios, and an indexing model that distinguishes agent UIDs from array positions. Starsim has been used to model domains ranging from family planning and primary health care to HIV and tuberculosis. Since the diseases themselves are often very complicated, the Starsim models built to model them can also be very complicated. Combined with a rapidly evolving API and a relatively small training-data footprint, this presents a challenge to AI tools that compounds the usual difficulties of limited context windows and out-of-date training data.

### Starsim-AI

We created a set of agent tools to improve domain-specific performance, called [Starsim-AI](https://github.com/starsimhub/starsim_ai). Specifically, we added Model Context Protocol (MCP) servers for Starsim and [Sciris](https://docs.sciris.org/en/latest/) [@sciris] (a scientific Python library used widely in the codebase). We also created a set of "skills" for Starsim, which consist of problem-solving and feature-oriented Markdown files. Each skill carries a short natural-language description that the agent uses to decide when the skill is relevant, plus a body that is loaded into context only when triggered — a form of progressive disclosure that keeps the agent's working context small until specialized knowledge is needed.

The skills fall into four groups. The largest is a set of *developer* skills, each covering one Starsim subsystem: getting started, configuring the `Sim`, diseases, contact networks, interventions, demographics, probability distributions, calibration, multi-disease connectors, analyzers, the time and units system, random number generation, agent indexing, performance profiling, running and comparing multiple simulations, and building non-standard (e.g. compartmental) models. A second group of *style* skills encodes Starsim's conventions for Python code, testing, documentation, and overall design philosophy, so that generated code reads like code a core developer would write. The remaining skills cover the companion [Sciris](https://docs.sciris.org/en/latest/) utility library and the [STIsim](https://github.com/starsimhub/stisim) extension for sexually transmitted infections. These skills were created by Claude Code based on the Starsim [tutorials](https://docs.starsim.org/tutorials) and [user guide](https://docs.starsim.org/user_guide). They were then manually reviewed and revised by Starsim core developers for accuracy and completeness.

### Evaluation suite

We created a hand-written "Starsim exam"
[evaluation suite](https://github.com/starsimhub/scipy2026_starsim_ai) designed to test knowledge about Starsim. Although used here for evaluating LLM performance, it is written in the style of a university final exam paper, and is applicable to both human and AI test-takers. The exam comprises five questions — Basics, Sim behavior, Modules, Advanced topics, and Miscellaneous — subdivided into roughly 30 individually-marked sub-questions worth 301 marks in total, and is designed to take a skilled human approximately three hours. The exam is open-ended and code-centric: most sub-questions require the test-taker to write runnable Starsim code, produce figures, and explain the resulting dynamics in prose, with marks awarded by a separate marking scheme (described below). Questions span the difficulty range from recall ("describe what Starsim is and does") to substantial modeling tasks (e.g. implementing both agent-based and compartmental SIRS models from base classes and quantifying their agreement, worth 50 marks).

As a representative example, sub-question 1.2.4 reads: *"Run a simulation with no network or disease but with 1000 agents and demographics enabled. Export the sim's people to a dataframe. At the end of the simulation, who is the oldest female?"* Answering it correctly requires knowing that demographics can be simulated without any disease, how to enable births and deaths, and how to introspect the resulting population — a combination that is easy to describe but trips up models lacking current Starsim knowledge.

Question 5 (Miscellaneous) is deliberately constructed to probe exam integrity: its sub-questions cannot be answered reliably from a model's training data alone. For instance, "What update was made in the latest release of Starsim?" requires consulting the current changelog, and "What are the six anti-patterns to avoid when working with networks?" is documented only in the Starsim user guide. A model that fabricates a plausible-sounding answer rather than grounding it in an authoritative source (via web search or the Starsim-AI plugin) reveals itself, letting us distinguish genuine tool-grounded knowledge from confident hallucination.

### Experimental design

We ran the evaluation suite using four Anthropic models (Haiku 4.6, Sonnet 4.6, Opus 4.6, and Opus 4.8) and two OpenAI models (GPT-5.4-mini and GPT-5.5). For each model, we ran them in three modes: baseline (answering questions immediately), agentic (allowing multi-turn answers, executing code, etc.), and agentic + Starsim-AI (with access to the Starsim skills).

Answers were graded automatically by an LLM-based marking agent rather than by hand. For each completed exam, we launched one autonomous marking agent per question, in parallel; each agent was given the question, the official solution and marking scheme, and the test-taker's submitted answer (including any figures). Working in the answer's scratch directory, the marker could re-run the submitted code to verify claims, but awarded only the marks defined by the scheme, checking off each criterion with a one-line justification and producing a per-question subtotal and an overall percentage. Using the marking scheme as a fixed rubric in this way keeps grading consistent across the many model/mode combinations and reduces the variance inherent in free-form LLM judging.

**Todo:**
- [ ] Describe how many times they were rerun (awaiting run data/manifests)

## Results

TBC -- results don't currently make a lot of sense!

**Todo:**
- [ ] Finalize a set of results that make sense
- [ ] Decide what figures to include

## Discussion

TBC

**Todo:**
- [ ] Discuss importance of model evolution (e.g. Opus 4.8 >> Sonnet 4.5)

<!-- [PLACEHOLDER: expand on implications of results. Why does tool access
matter more than model choice? What kinds of skills were most impactful?
Limitations of the evaluation suite (coverage, generalizability, etc.).] -->

## Conclusion

TBC
