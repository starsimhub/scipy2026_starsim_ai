# %%
from rich import print

import numpy as np
import seaborn as sns
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
# Figure 1: Pass rate vs. allowed time to solve per problem for agent benchmark
task_name = 'starsim_agent_benchmark'
df_task = df_eval[df_eval['task_name'] == task_name]
df_task = df_task[np.logical_not(df_task['task_arg_with_background'])]
df_task = df_task.sort_values(by='task_arg_request_timeout')
df_task = df_task.rename(columns={'task_arg_agent_url': 'w/ Plugin', 'task_arg_request_timeout': 'Time limit'})
df_task = df_task.replace({'w/ Plugin': {'http://localhost:9100': 'No', 'http://localhost:9101': 'Yes'}})

fig = plt.figure(figsize=(5,3))
ax = plt.gca()
sns.barplot(x='Time limit', y='score_headline_value', data=df_task, ax=ax, hue='w/ Plugin')
for container in ax.containers:
    ax.bar_label(container, fontsize=10, fmt='%.2f');
ax.set_ylim(0, 1)
ax.set_xlabel('Allowed time to solve per problem (seconds)')
ax.set_ylabel('Pass rate')
ax.set_title('Starsim Agent Benchmark')

# %%
# Figure 2: Pass rate vs. model for LLM benchmark
task_name = 'starsim_benchmark'
df_task = df_eval[df_eval['task_name'] == task_name]
df_task = df_task.sort_values(by='model')

fig = plt.figure(figsize=(5,3))
ax = plt.gca()
sns.barplot(x='model', y='score_headline_value', data=df_task, ax=ax, hue='task_arg_with_background')
for container in ax.containers:
    ax.bar_label(container, fontsize=10, fmt='%.2f');
ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
ax.set_ylim(0, 1)
ax.set_xlabel('Model')
ax.set_ylabel('Pass rate')
ax.set_title('Starsim LLM Benchmark')

# %%
