# **Vibes, meet rigor: Evaluating and improving AI performance on complex scientific code**

Cliff Kerr¹, Katherine Rosenfeld¹, Jessica Lundin¹, Robyn Stuart¹, Romesh Abeysuriya²

¹ Bill & Melinda Gates Foundation, Seattle, USA; ² Burnet Institute, Melbourne, Australia

2 March 2026

 
# **Abstract ("around 100 words or less")**

Scientists apply rigorous methods to their research, but rarely to the AI tools they use to write code. We tested different LLM models in combination with domain-specific tools (including MCP servers and skills) to find the optimal combination for writing complex domain-specific code. We created a quantitative proficiency test for Starsim, a disease modeling framework, and evaluated different combinations of models and tools. While Claude Opus outperformed other models, access to tools improved performance more than choosing the best model. Thus, to improve LLM performance on domain-specific problems, we recommend developing a set of tools with the help of quantitative evaluation.

# **Description ("roughly 500 words")**

**Background**  
Scientists are often decidedly unscientific about choosing AI tools to help them write code. They know these tools are helpful, but except for trying out different models, they rarely perform controlled evaluations to check whether other changes to their AI workflow produce significantly better results. This is because writing and executing these evaluations is typically time-consuming, the results of the evaluations are difficult to interpret and quantify, and AI workflows and tooling are evolving rapidly. Here we describe our process for quantitatively testing our assumptions about how to build a good AI assistant.

**Methods**  
Our team models infectious diseases using [Starsim](https://starsim.org/), a high-performance agent-based modeling library built on NumPy, SciPy, and Numba. Specifically, Starsim includes modules for different diseases, transmission networks, and interventions (such as vaccines). Starsim has been used to model domains ranging from family planning and primary health care to HIV and tuberculosis. Since the diseases themselves are often very complicated, the Starsim models built to model them can also be very complicated. This presents a challenge to AI tools due to limited context windows and out-of-date information.

We created a "Starsim exam" [evaluation suite](https://github.com/starsimhub/scipy2026_starsim_ai/tree/main/problems) based on Starsim’s online documentation. This benchmark is administered using [Inspect.ai](http://Inspect.ai) and follows the structure of the [SciCode](https://arxiv.org/abs/2407.13168) benchmark with a modular approach to question building and evaluation via unit tests.

Next, we created a set of agent tools to improve domain-specific performance, called [Starsim-AI](https://github.com/starsimhub/starsim_ai). Specifically, we added MCP servers for Starsim and [Sciris](https://docs.sciris.org/en/latest/) (a scientific Python library used widely in the codebase). We also created a set of "skills" for Starsim, which consist of problem-solving and feature-oriented Markdown files covering topics including statistical distributions, simulation construction, and calibration. These skills were created by Claude Code based on the Starsim [tutorials](https://docs.starsim.org/tutorials) and [user guide](https://docs.starsim.org/user_guide). They were then manually reviewed and revised by Starsim core developers for accuracy and completeness.

Finally, we ran the evaluation suite using two Anthropic models (Claude Sonnet 4.6 and Claude Opus 4.6), both with and without access to the Starsim-AI tools, and two OpenAI models (GPT-5.2 and GPT-5 mini, which did not have access to the tools).

**Results**  
Performance on the evaluation varied widely among the no-tool models, from 17% with GPT-5 mini to 70% with Claude Opus 4.6. Adding the full skillset in agent mode increased performance to 78% for Sonnet 4.6 and 91% for Opus 4.6. When given unlimited solving time, adding skills reduced task completion time by up to 20%. Conversely, when given limited solving time (2 minutes), Starsim-AI increased Opus 4.6's performance from 13% to 65%. Across models, task performance was strongly correlated with token usage (R²=0.61), but adding skills only marginally increased token usage (1-3%).

**Conclusions**  
For our domain-specific problem, providing custom skills and MCP servers reduced the error rate by a factor of three (from 30% to 9%) and reduced task completion time by 20%. We recommend creating a structured problem set for use with a quantitative evaluation tool, as this can help develop the set of domain-specific tools that most effectively improves LLM performance.

# **Notes to organizer**

I gave a [talk at SciPy 2022](https://www.youtube.com/watch?v=eZJ0FaPw2Gs) in Austin on [Covasim](https://conference.scipy.org/proceedings/scipy2022/pdfs/cliff_kerr.pdf), a COVID-19 model. I also gave a [talk at SciPy 2024](https://www.youtube.com/watch?v=3uMTnn8xC8w) on [Starsim](https://starsim.org/), and a lightning talk on [Sciris](https://docs.sciris.org/en/latest/).

**Track:**   
AI

**Keywords:**  
AI evaluation, agent-based model, disease modeling, Starsim, Sciris, Inspect.ai, SciCode, Claude
