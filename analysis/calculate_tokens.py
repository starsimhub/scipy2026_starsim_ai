"""
One-off script to calculate token usage ratio
"""

import sciris as sc
import matplotlib.pyplot as plt

filename = 'results_2026-03-04.json'

json = sc.loadjson(filename)

r = sc.objdict({k:sc.objdict(v) for k,v in json.items()})

df = sc.dataframe(json.values())
df = df.sort_values('score') #(['model', 'plugin'])

plt.scatter(df.tokens, df.score)

lr = sc.linregress(df.tokens, df.score, full=True)

print(lr)
print(df)

print('Extra token usage')
tk = sc.objdict()

keys = list(r.keys())
agent_keys = {k: r[k] for k in keys if 'agent' in k}
tk.sonnet0 = [v.tokens for k, v in agent_keys.items() if 'sonnet' in k and 'plugin' not in k][0]
tk.sonnet1 = [v.tokens for k, v in agent_keys.items() if 'sonnet' in k and 'plugin' in k][0]
tk.opus0   = [v.tokens for k, v in agent_keys.items() if 'opus' in k and 'plugin' not in k][0]
tk.opus1   = [v.tokens for k, v in agent_keys.items() if 'opus' in k and 'plugin' in k][0]

sonnet = ((tk.sonnet1/tk.sonnet0) - 1)*100
opus = ((tk.opus1/tk.opus0) - 1)*100

print(f'Sonnet: {sonnet:n}%')
print(f'Opus: {opus:n}%')