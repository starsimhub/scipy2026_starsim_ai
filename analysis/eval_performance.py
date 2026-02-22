# %%
from rich import print

import numpy as np
import matplotlib.pyplot as plt
from inspect_ai.analysis import evals_df, samples_df

df_eval = evals_df('../logs')
df_samples = samples_df('../logs')

# %%
print(df_eval.columns)
df_eval.head()
print(f"df_eval.shape: {df_eval.shape}")

# %%
task_names = df_eval['task_name'].unique()
print(task_names)
# %%
# Figure 1: Pass rate vs. allowed time to solve per problem
task_name = 'starsim_agent_benchmark'
df_task = df_eval[df_eval['task_name'] == task_name]
df_task = df_task.sort_values(by='task_arg_request_timeout')

fig = plt.figure(figsize=(5,3))
ax = plt.gca()
ax.bar(np.arange(len(df_task)),df_task['score_headline_value'], color='xkcd:blue')
ax.set_xticks(np.arange(len(df_task)))
ax.set_xticklabels(df_task['task_arg_request_timeout'])
ax.set_ylim(0, 1)
ax.set_xlabel('Allowed time to solve per problem (seconds)')
ax.set_ylabel('Pass rate')
ax.set_title('Starsim Agent Benchmark')

# %%
task_name = 'starsim_benchmark'
df_task = df_eval[df_eval['task_name'] == task_name]
df_task = df_task.sort_values(by='model')

fig = plt.figure(figsize=(5,3))
ax = plt.gca()
ax.bar(np.arange(len(df_task)),df_task['score_headline_value'], color='xkcd:lightblue')
ax.set_xticks(np.arange(len(df_task)))
ax.set_xticklabels(df_task['model'], rotation=45)
ax.set_ylim(0, 1)
ax.set_xlabel('Model')
ax.set_ylabel('Pass rate')
ax.set_title('Starsim LLM Benchmark')
