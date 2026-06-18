---
# Ensure that this title is the same as the one in `myst.yml`
title: "Vibes, meet rigor: Evaluating and improving AI performance on complex scientific code"
abstract: |
  Scientists apply rigorous methods to their research, but rarely to the AI tools they use to write code. We tested different LLM models in combination with domain-specific tools (including MCP servers and skills) to find the optimal combination for writing complex domain-specific code. We created a quantitative proficiency test for Starsim, a disease modeling framework, and evaluated different combinations of models and tools. While Claude Opus outperformed other models, access to tools allowed cheaper models (like Haiku) to perform almost as well as more expensive ones. Thus, to improve LLM performance on domain-specific problems, we recommend developing a set of tools with the help of quantitative evaluation.
---

## Introduction

Scientists are often decidedly unscientific about choosing AI tools to help
them write code. They know these tools are helpful, but except for trying out
different models, they rarely perform controlled evaluations to check whether
other changes to their AI workflow produce significantly better results. This
is because writing and executing these evaluations is typically time-consuming,
the results of the evaluations are difficult to interpret and quantify, and AI
workflows and tooling are evolving rapidly. Here we describe our process for
quantitatively testing our assumptions about how to build a good AI assistant.

**Todo:**
- [ ] Cite other benchmarking/eval suites, e.g. Terminal Bench

## Methods

### Starsim

Our team models infectious diseases using [Starsim](https://starsim.org/)
[@starsim], a high-performance agent-based modeling library built on NumPy
[@numpy], SciPy [@scipy], and Numba. Specifically, Starsim includes modules
for different diseases, transmission networks, and interventions (such as
vaccines). Starsim has been used to model domains ranging from family planning
and primary health care to HIV and tuberculosis. Since the diseases themselves
are often very complicated, the Starsim models built to model them can also be
very complicated. This presents a challenge to AI tools due to limited context
windows and out-of-date training data.

**Todo:**
- [ ] Say more about Starsim

### Starsim-AI

We created a set of agent tools to improve domain-specific performance,
called [Starsim-AI](https://github.com/starsimhub/starsim_ai). Specifically,
we added Model Context Protocol (MCP) servers for Starsim and
[Sciris](https://docs.sciris.org/en/latest/) [@sciris] (a scientific Python
library used widely in the codebase). We also created a set of "skills" for
Starsim, which consist of problem-solving and feature-oriented Markdown files
covering topics including statistical distributions, simulation construction,
and calibration. These skills were created by Claude Code based on the Starsim
[tutorials](https://docs.starsim.org/tutorials) and
[user guide](https://docs.starsim.org/user_guide). They were then manually
reviewed and revised by Starsim core developers for accuracy and completeness.

**Todo:**
- [ ] Say more about the individual skills

### Evaluation suite

We created a hand-written "Starsim exam"
[evaluation suite](https://github.com/starsimhub/scipy2026_starsim_ai/tree/main/problems) designed to test knowledge about Starsim. Although used here for evaluating LLM performance, it is written in the style of a university final exam paper, and is applicable to both human and AI test-takers.

**Todo:**
- [ ] Say more about the exam, eg number of questions, etc.
- [ ] Include an example question
- [ ] Describe question 5, designed to test exam integrity

### Experimental design

We ran the evaluation suite using four Anthropic models (Haiku 4.6, Sonnet 4.6, Opus 4.6, and Opus 4.8) and two OpenAI models (GPT-5.4-mini and GPT-5.5). For each model, we ran them in three modes: baseline (answering questions immediately), agentic (allowing multi-turn answers, executing code, etc.), and agentic + Starsim-AI (with access to the Starsim skills).

**Todo:**
- [ ] Describe how many times they were rerun
- [ ] Describe judges

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
