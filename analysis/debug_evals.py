"""
Print extra debugging information about the evals
"""

import sciris as sc
from inspect_ai.log import read_eval_log
files = sc.getfilelist('../logs/*.eval')
print(f'Analyzing:\n{sc.newlinejoin(files)}')

for file in files:
    sc.heading(file)

    log = read_eval_log(file)  # or .eval file

    # Overall results
    sc.printgreen(log.results)           # EvalResults with metrics
    print(log.results.scores)    # list of EvalScore objects (one per scorer)

    # Per-sample details
    for sample in log.samples:
        sc.printcyan(sample.id)                    # sub_step_id
        # print(sample.scores)               # dict of scorer → Score
        if 'starsim_scorer' in sample.scores:
            score = sample.scores["starsim_scorer"]
        elif 'agent_scorer' in sample.scores:
            score = sample.scores["agent_scorer"]
        else:
            print('No starsim or agent scorer, but', sample.scores.keys())
            continue
        print(score.value)                 # 1.0 or 0.0
        print(score.explanation)           # error messages or "All tests passed"
        print(score.metadata)             # tests_passed, tests_total, sub_step_id, problem_id
        print(sample.messages)            # full message transcript