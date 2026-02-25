"""
Evaluate performance of different models/configurations.
"""

import numpy as np
import sciris as sc
from rich import print
import matplotlib.pyplot as plt
from inspect_ai.analysis import evals_df

df_eval = evals_df('../logs')

df_eval.head()
print(df_eval.columns)
print(f"df_eval.shape: {df_eval.shape}")

# task_name = 'starsim_agent_benchmark'
# df_task = df_eval[df_eval['task_name'] == task_name]
df_task = df_eval # TODO: fix
df_task = df_task.sort_values(by='model')

sc.options(dpi=150)
fig = plt.figure(figsize=(8,8))
ax = plt.gca()
ax.barh(np.arange(len(df_task)), df_task['score_headline_value'], color='xkcd:lightblue')
ax.set_yticks(np.arange(len(df_task)))
ax.set_yticklabels(df_task['model'] + df_task['task_arg_with_plugin'].apply(str))
ax.set_xlim(0, 1)
ax.set_ylabel('Model')
ax.set_xlabel('Pass rate')
ax.set_title('Starsim LLM Benchmark')

sc.figlayout()

plt.show()


# # Figure 1: Pass rate vs. allowed time to solve per problem
# task_name = 'starsim_agent_benchmark'
# df_task = df_eval[df_eval['task_name'] == task_name]
# df_task = df_task.sort_values(by='task_arg_request_timeout')

# fig = plt.figure(figsize=(5,3))
# ax = plt.gca()
# ax.bar(np.arange(len(df_task)),df_task['score_headline_value'], color='xkcd:blue')
# ax.set_xticks(np.arange(len(df_task)))
# ax.set_xticklabels(df_task['task_arg_request_timeout'])
# ax.set_ylim(0, 1)
# ax.set_xlabel('Allowed time to solve per problem (seconds)')
# ax.set_ylabel('Pass rate')
# ax.set_title('Starsim Agent Benchmark')