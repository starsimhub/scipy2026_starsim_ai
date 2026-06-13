---
# Ensure that this title is the same as the one in `myst.yml`
title: "Vibes, meet rigor: Evaluating and improving AI performance on complex scientific code"
abstract: |
  Scientists apply rigorous methods to their research, but rarely to the AI
  tools they use to write code. We tested different LLM models in combination
  with domain-specific tools (including MCP servers and skills) to find the
  optimal combination for writing complex domain-specific code. We created a
  quantitative proficiency test for Starsim, a disease modeling framework, and
  evaluated different combinations of models and tools. While Claude Opus
  outperformed other models, access to tools improved performance more than
  choosing the best model. Thus, to improve LLM performance on domain-specific
  problems, we recommend developing a set of tools with the help of quantitative
  evaluation.
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

<!-- [PLACEHOLDER: expand introduction with motivation, related work, and
contributions. Consider citing prior AI coding benchmarks, e.g. SciCode
[@scicode], HumanEval, etc.] -->

## Methods

### Domain and evaluation suite

Our team models infectious diseases using [Starsim](https://starsim.org/)
[@starsim], a high-performance agent-based modeling library built on NumPy
[@numpy], SciPy [@scipy], and Numba. Specifically, Starsim includes modules
for different diseases, transmission networks, and interventions (such as
vaccines). Starsim has been used to model domains ranging from family planning
and primary health care to HIV and tuberculosis. Since the diseases themselves
are often very complicated, the Starsim models built to model them can also be
very complicated. This presents a challenge to AI tools due to limited context
windows and out-of-date training data.

We created a "Starsim exam"
[evaluation suite](https://github.com/starsimhub/scipy2026_starsim_ai/tree/main/problems)
based on Starsim's online documentation. This benchmark is administered using
[Inspect.ai](https://inspect.ai) [@inspectai] and follows the structure of the
[SciCode](https://arxiv.org/abs/2407.13168) [@scicode] benchmark, with a
modular approach to question building and evaluation via unit tests.

<!-- [PLACEHOLDER: add description of how many problems, what topics they
cover, how the unit tests are structured, and any example problems or a
figure showing the benchmark structure.] -->

### Starsim-AI toolset

Next, we created a set of agent tools to improve domain-specific performance,
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

### Experimental design

We ran the evaluation suite using two Anthropic models (Claude Sonnet 4.6 and
Claude Opus 4.6), both with and without access to the Starsim-AI tools, and
two OpenAI models (GPT-5.2 and GPT-5 mini, which did not have access to the
tools).

<!-- [PLACEHOLDER: describe evaluation setup in more detail — number of runs
per problem, timeout settings ("unlimited" vs 2-minute conditions), compute
environment, and how scores were aggregated across tasks.] -->

## Results

Performance on the evaluation varied widely among the no-tool models, from
17% with GPT-5 mini to 70% with Claude Opus 4.6. Adding the full Starsim-AI
skillset in agent mode increased performance to 78% for Claude Sonnet 4.6 and
91% for Claude Opus 4.6. Results are summarized in @tbl:results.

```{list-table} Evaluation scores by model and tool condition.
:label: tbl:results
:header-rows: 1
* - Model
  - Tools
  - Score (unlimited time)
  - Score (2-min limit)
* - GPT-5 mini
  - None
  - 17%
  - —
* - GPT-5.2
  - None
  - <!-- [PLACEHOLDER] -->
  - —
* - Claude Sonnet 4.6
  - None
  - <!-- [PLACEHOLDER] -->
  - <!-- [PLACEHOLDER] -->
* - Claude Sonnet 4.6
  - Starsim-AI
  - 78%
  - <!-- [PLACEHOLDER] -->
* - Claude Opus 4.6
  - None
  - 70%
  - 13%
* - Claude Opus 4.6
  - Starsim-AI
  - 91%
  - 65%
```

When given unlimited solving time, adding skills reduced task completion time
by up to 20%. Conversely, when given limited solving time (2 minutes),
Starsim-AI increased Claude Opus 4.6's performance from 13% to 65%. Across
models, task performance was strongly correlated with token usage
($R^2 = 0.61$), but adding skills only marginally increased token usage (1–3%).

<!-- [PLACEHOLDER: add a figure showing performance vs. token usage
correlation, and/or bar chart comparing models. Replace figure1.png and
figure2.png with actual result figures.] -->

:::{figure} figure1.png
:label: fig:results
<!-- [PLACEHOLDER: replace with actual results figure — e.g., bar chart of
scores by model/condition.] -->
Placeholder figure: evaluation scores by model and tool condition.
:::

:::{figure} figure2.png
:label: fig:tokens
<!-- [PLACEHOLDER: replace with actual figure — e.g., scatter plot of
performance vs. token usage (R²=0.61).] -->
Placeholder figure: task performance vs. token usage across models.
:::

## Discussion

<!-- [PLACEHOLDER: expand on implications of results. Why does tool access
matter more than model choice? What kinds of skills were most impactful?
Limitations of the evaluation suite (coverage, generalizability, etc.).] -->

## Conclusion

For our domain-specific problem, providing custom skills and MCP servers
reduced the error rate by a factor of three (from 30% to 9%) and reduced task
completion time by 20%. We recommend creating a structured problem set for use
with a quantitative evaluation tool, as this can help develop the set of
domain-specific tools that most effectively improves LLM performance.
