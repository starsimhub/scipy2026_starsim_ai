# **Vibes, meet rigor: Evaluating and improving AI performance on complex scientific code**

Cliff Kerr1, Katherine Rosenfeld1, Jessica Lundin1, Robyn Stuart1, Romesh Abeysuriya2

1 Bill & Melinda Gates Foundation, Seattle, USA; 2 Burnet Institute, Melbourne, Australia

23 February 2026

# **Abstract ("around 100 words or less")**

Scientists apply rigorous methods to their research, but rarely to the AI tools they use to write code. We tested different LLM models in combination with domain-specific tools (including MCP servers and additional skillsets) to find the optimal combination for writing complex domain-specific code. We created a quantitative proficiency test for Starsim, a disease modeling framework, and evaluated different combinations of models and tools. We found that Claude Opus outperformed other models, but access to tools provided a bigger performance boost than choosing the best model. Thus, to enhance LLM performance on domain-specific problems, we recommend using quantitative evaluation to develop a set of tools.

# **Description ("roughly 500 words")**

**Background**  
Scientists are often decidedly unscientific about choosing AI tools to help them write code. They have a sense that these tools are helpful, but except for trying out different models, they rarely perform controlled tests to check whether other changes to their AI workflow would produce significantly better results. This is because writing and executing these tests is typically time-consuming, the results of the tests are difficult to interpret and quantify, and AI workflows and tooling are evolving rapidly. Here we describe our process for quantitatively testing our assumptions about what makes for a good AI assistant.

**Methods**  
We build models of infectious diseases using [Starsim](https://starsim.org/), an agent-based modeling framework for Python. Specifically, Starsim includes modules for disease dynamics, transmission networks, births and deaths, and health interventions (including testing, treatment, and vaccines). Starsim has been used to model health systems and diseases ranging from family planning and primary health care to HIV and tuberculosis. Due to the complexity of the diseases being modeled, Starsim models are often very complicated. In addition, the Starsim framework itself has many features. These present a challenge to AI tools due to limited context windows and out-of-date information.

First, we created a "Starsim exam" based on Starsim’s online documentation. This evaluation benchmark is administered using [Inspect.ai](http://Inspect.ai) and follows the structure of the [SciCode](https://arxiv.org/abs/2407.13168) benchmark with a modular approach to question building and evaluation via unit tests. A central goal of this benchmark is to measure how well an agent can leverage Starsim as a library to solve modeling problems, rather than writing disease models from scratch.

Second, we created a set of tools that we thought would help improve performance, called [Starsim-AI](https://github.com/starsimhub/starsim_ai). We added MCP servers for Starsim (and [Sciris](https://docs.sciris.org/en/latest/), a scientific Python library used widely in the codebase). We also created a skillset for Starsim, which consists of problem-solving and feature-oriented Markdown files. These skills were created by Claude Code based on the Starsim docs, and then manually reviewed and revised by Starsim core developers.

Finally, we ran the evaluation using two Anthropic models (Claude Sonnet 4.6 and Claude Opus 4.6 1M context), and two OpenAI models (gpt-5.2, gpt-5-mini) with and without access to the Starsim-AI tools.

**Results**  
Performance on the evaluation varied widely among the no-tool models, from 17% with gpt-5-mini to 70% with Claude Opus 4.6. Adding the full skillset in agent mode increased performance to 78% for Sonnet 4.6 and 91% for Opus 4.6. When given unlimited solving time, adding skills also reduced task completion time by up to 20%. Conversely, when given limited solving time (2 minutes), skills increased performance from 13% to 65%.

**Conclusions**  
For domain-specialized libraries like Starsim, bespoke skills and MCP servers improved AI performance by 21% and reduced task completion time by 20%. We recommend using a structured problem set paired with a quantitative evaluation tool to help users develop the set of domain-specific tools that most effectively improves LLM performance.

# **Notes to organizer**

I gave a [talk at SciPy 2022](https://www.youtube.com/watch?v=eZJ0FaPw2Gs) in Austin on [Covasim](https://conference.scipy.org/proceedings/scipy2022/pdfs/cliff_kerr.pdf), a COVID-19 model. I also gave a [talk at SciPy 2024](https://www.youtube.com/watch?v=3uMTnn8xC8w) on Starsim, and a lightning talk on Sciris.

**Track:**   
AI

**Keywords:**  
AI evaluation  
