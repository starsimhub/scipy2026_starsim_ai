"""
Quantify results for the abstract
"""

import sciris as sc
from datetime import datetime
from inspect_ai.log import read_eval_log
files = sc.getfilelist('../logs/*.eval')
print(f'Analyzing:\n{sc.newlinejoin(files)}')

def shorten_model(model):
    if 'sonnet' in model:
        return 'claude-sonnet-4.6'
    elif 'opus' in model:
        return 'claude-opus-4.6'
    elif '5.2' in model:
        return 'gpt-5.2'
    elif 'mini' in model:
        return 'gpt-5-mini'

r = sc.objdict()

for file in files:
    sc.heading(file)
    entry = sc.objdict()

    # Load file
    log = read_eval_log(file)

    # Get flags
    entry.model = log.eval.model
    entry.plugin = log.eval.task_args.get('with_plugin', False)

    # Construct key: "{model}" or "{model}+plugin"
    key = shorten_model(entry.model)
    key += log.eval.task_file
    if entry.plugin:
        key += ' + plugin'

    # Get time
    start = datetime.fromisoformat(log.stats.started_at)
    stop = datetime.fromisoformat(log.stats.completed_at)
    entry.time = (stop - start).total_seconds()

    # Get tokens
    entry.tokens = sum(u.total_tokens for u in log.stats.model_usage.values())

    # Get overall result
    entry.score = log.results.scores[0].metrics['mean'].value

    # Store results
    if key in r:
        raise Exception('Already present')
    r[key] = entry

df = sc.dataframe.from_dict(r, orient='index')
df.index.name = 'config'
df.disp()
