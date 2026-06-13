# Question 4: Advanced topics

## 4.1: Profiling and debugging [20 marks]

##### 4.1.1. The analyzer below tracks the cumulative number of timesteps each agent spends infected. It produces correct results, but it makes the simulation much slower than it should be. Using Starsim's profiling and debugging tools, (a) identify which part of the simulation is the bottleneck, (b) explain why it is slow, and (c) rewrite the analyzer so that it produces identical results but runs significantly faster. Report the speedup. [12 marks]

```py
import numpy as np
import starsim as ss

class ExposureTracker(ss.Analyzer):
    """ Track the cumulative number of timesteps each agent spends infected """
    def init_post(self):
        super().init_post()
        self.exposure = np.zeros(len(self.sim.people))
        return

    def step(self):
        infected = self.sim.diseases.sis.infected
        uids = self.sim.people.uid
        for i in range(len(uids)):
            if infected[uids[i]]:
                self.exposure[i] += 1
        return

sim = ss.Sim(diseases='sis', networks='random', n_agents=10_000,
             start=0, dur=ss.days(100), dt=ss.days(1.0), verbose=0,
             analyzers=ExposureTracker(), rand_seed=1)
sim.run()
```
---

##### 4.1.2 The following code contains at least 8 bugs or inefficient uses of Starsim. Write the corrected version of the code, and explain what the mistakes were and what their consequences would be. The command to test the code is at the end of the code block (you do not need to check the test running code for bugs). [8 marks]

```py
import starsim as ss
import numpy as np

class Gonorrhea(ss.Infection):

    def __init__(self, **kwargs):
        super().__init__()
        self.define_pars(
            beta = ss.perday(0.5),
            dur_inf   = ss.Normal(mean=10, std=0.6),
            p_symp    = 0.5,
            p_clear   = 0.7,
            init_prev = ss.bernoulli(p=0.1),
        )
        self.update_pars(**kwargs)

        self.define_states(
            ss.BoolState('symptomatic', label='Symptomatic'),
            ss.FloatArr('ti_clearance', label='Time of clearance'),
        )
        return

    def step_state(self):
        """ Natural clearance """
        ti = self.sim.t.ti
        clearances = np.where(self.ti_clearance <= ti)[0]
        self.ti_clearance[clearances] = ti
        self.susceptible[clearances] = True
        self.infected[clearances] = False
        self.symptomatic[clearances] = False        
        return

    def set_prognoses(self, uids, sources=None):
        """ Natural history of gonorrhea for adult infection """
        super().set_prognoses(uids, sources)
        ti = self.sim.t.ti

        # Set infection status
        self.susceptible[uids] = False
        self.infected[uids] = True
        self.ti_infected[uids] = ti

        # Set infection status
        symp_uids = self.pars.p_symp.filter(uids)
        self.symptomatic[symp_uids] = True

        # Set natural clearance
        clear_uids = uids[self.pars.p_clear > np.random.random(len(uids))]
        dur = ti + float(ss.days(self.pars.dur_inf).rvs(clear_uids))
        self.ti_clearance[clear_uids] = dur
        return
    
# Code for testing
sim = ss.Sim(diseases=Gonorrhea(), networks=ss.MFNet(duration=ss.days(14)), dt=ss.days(1), dur=100)
sim.run()
sim.plot()
```


## 4.2: Rates, probabilities, and durations [19 marks]

##### 4.2.1. The word "rate" is heavily overloaded in epidemiology. You are modeling Disease X. Translate each of the following descriptions into the most appropriate Starsim parameter representation (e.g. `ss.peryear`, `ss.freqperday`, `ss.prob`, `ss.days`, ...). State the numeric value and time unit explicitly, and justify each choice in one line. [15 marks]

1. The crude death rate for the population is 8 per 1000 people.
2. The infection fatality rate is 0.7%.
3. Upon infection with Disease X, a person gains immunity that decays exponentially with a half-life of 3 months.
4. The contact rate is 20 people per day.
5. The average duration of infection is 10 days.
6. On average, an infected person infects 2.5 others.
7. A cohort study finds that 2% of undiagnosed cases are detected within 30 days.

##### 4.2.2. The crude death rate (item 1) could be written as either `ss.peryear(0.008)` or `ss.probperyear(0.008)`. (a) Explain what each means and how many of 1000 people die after one year under each. (b) For what magnitude of rate does the choice matter? [4 marks]
