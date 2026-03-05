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

tk.sonnet0 = r[2].tokens
tk.sonnet1 = r[1].tokens
tk.opus0 = r[0].tokens
tk.opus1 = r[3].tokens

sonnet = ((tk.sonnet1/tk.sonnet0) - 1)*100
opus = ((tk.opus1/tk.opus0) - 1)*100

print(f'Sonnet: {sonnet:n}%')
print(f'Opus: {opus:n}%')