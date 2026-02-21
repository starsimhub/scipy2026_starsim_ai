# starsim_t4

## starsim_t4.1

### Description
Explore how disease-induced mortality (p_death) affects SIR epidemic outcomes. Run multiple SIR simulations with different mortality probabilities and compare the cumulative number of infections and final number of recovered agents. Higher mortality should reduce the recovered population since more infected agents die.

### Background
The p_death parameter in Starsim's SIR model controls the probability that an infected agent dies from the disease instead of recovering. When p_death is 0, all infected agents eventually recover. When p_death is positive, a fraction of infected agents die, reducing the recovered population. This parameter is important for modeling diseases with significant case fatality rates. Disease parameters like dur_inf, beta, init_prev, and p_death can be passed directly to ss.SIR().

### Dependencies
- starsim

### Function Header
```python
def compare_mortality_rates(p_deaths: list[float], n_agents: int = 5_000, beta: float = 0.2, init_prev: float = 0.1, dur_inf: float = 10) -> dict[float, dict]:
```

### Docstring
```
Run SIR simulations with different mortality rates and compare outcomes.

Args:
    p_deaths: List of mortality probabilities to compare (e.g., [0.0, 0.2, 0.5]).
    n_agents: Number of agents to simulate.
    beta: Probability of transmission between contacts.
    init_prev: Initial proportion of the population that is infected.
    dur_inf: Duration of infection in years.

Returns:
    Dictionary mapping each p_death value to a dict containing:
        - 'cum_infections': cumulative infections at end of simulation
        - 'n_recovered': number of recovered agents at end of simulation
```

### Test Cases

#### Results should contain an entry for each p_death value
```python
results = compare_mortality_rates([0.0, 0.2, 0.5])
assert set(results.keys()) == {0.0, 0.2, 0.5}, 'Should have results for all p_death values'
```

#### Each result should contain cum_infections and n_recovered
```python
results = compare_mortality_rates([0.0])
assert 'cum_infections' in results[0.0], 'Should contain cum_infections'
assert 'n_recovered' in results[0.0], 'Should contain n_recovered'
```

#### Higher mortality should produce fewer recovered agents
```python
results = compare_mortality_rates([0.0, 0.5], n_agents=5_000)
assert results[0.0]['n_recovered'] > results[0.5]['n_recovered'], 'Higher mortality should reduce the recovered count'
```

#### All simulations should produce infections
```python
results = compare_mortality_rates([0.0, 0.2, 0.5])
assert all(v['cum_infections'] > 0 for v in results.values()), 'All simulations should produce some infections'
```

### Gold Solution
```python
def compare_mortality_rates(p_deaths: list[float], n_agents: int = 5_000, beta: float = 0.2, init_prev: float = 0.1, dur_inf: float = 10) -> dict[float, dict]:
    import starsim as ss
    results = {}
    for pd in p_deaths:
        sir = ss.SIR(beta=beta, init_prev=init_prev, dur_inf=dur_inf, p_death=pd)
        sim = ss.Sim(n_agents=n_agents, diseases=sir, networks='random')
        sim.run()
        results[pd] = {
            'cum_infections': float(sim.results.sir.cum_infections[-1]),
            'n_recovered': float(sim.results.sir.n_recovered[-1]),
        }
    return results
```
## starsim_t4.2

### Description
Create a custom SEIR (susceptible-exposed-infectious-recovered) disease model by subclassing Starsim's built-in SIR model. The SEIR model adds an exposed (latent) compartment: after transmission, agents enter an exposed state before becoming infectious. Define the new class with appropriate states, parameters, and state transition logic, then run a simulation with it.

### Background
The SEIR model extends SIR by adding an exposed (E) compartment between susceptible and infectious. This represents a latent period during which an agent has been infected but is not yet (fully) infectious. In Starsim, custom disease models are created by subclassing existing ones (e.g., ss.SIR). Key methods to override include: __init__ (to add parameters and states via define_pars and define_states), set_prognoses (to schedule state transitions when infection occurs), step_state (to execute scheduled transitions each timestep), and step_die (to clean up states when agents die). The 'infectious' property determines which agents can transmit the disease.

### Dependencies
- starsim

### Function Header
```python
def create_seir_sim(n_agents: int = 5_000, beta: float = 0.1, init_prev: float = 0.05, dur_exp: float = 0.5, dur_inf: float = 10, p_death: float = 0.0) -> ss.Sim:
```

### Docstring
```
Create and run a simulation with a custom SEIR disease model.

Define an SEIR class that extends ss.SIR by adding an exposed compartment.
New agents who are infected first become exposed, then transition to infectious
after a latent period (dur_exp). The class should:
  - Add an 'exposed' BoolState and 'ti_exposed' FloatArr state
  - Add a 'dur_exp' parameter (using ss.lognorm_ex distribution)
  - Override set_prognoses to route new infections through the exposed state
  - Override step_state to handle exposed -> infected transitions
  - Override step_die to clear the exposed state for dying agents

Args:
    n_agents: Number of agents to simulate.
    beta: Probability of transmission between contacts.
    init_prev: Initial proportion of the population that is infected.
    dur_exp: Mean duration of the exposed (latent) period in years.
    dur_inf: Duration of infection in years.
    p_death: Probability of death among infected agents.

Returns:
    A Starsim Sim object that has been run to completion with the SEIR disease.
```

### Test Cases

#### Simulation should have an SEIR disease
```python
sim = create_seir_sim()
assert hasattr(sim.diseases, 'seir'), 'Simulation should have an SEIR disease'
```

#### SEIR results should include the exposed compartment
```python
sim = create_seir_sim()
assert 'n_exposed' in sim.results.seir, 'SEIR results should track n_exposed'
```

#### Simulation should produce infections
```python
sim = create_seir_sim()
assert sim.results.seir.cum_infections[-1] > 0, 'There should be at least some infections'
```

#### Population size should match n_agents parameter
```python
sim = create_seir_sim(n_agents=1_000)
assert sim.pars.n_agents == 1_000, 'Population size should match n_agents'
```

### Gold Solution
```python
def create_seir_sim(n_agents: int = 5_000, beta: float = 0.1, init_prev: float = 0.05, dur_exp: float = 0.5, dur_inf: float = 10, p_death: float = 0.0) -> ss.Sim:
    import starsim as ss

    class SEIR(ss.SIR):
        def __init__(self, pars=None, *args, **kwargs):
            super().__init__()
            self.define_pars(
                dur_exp=ss.lognorm_ex(0.5),
            )
            self.update_pars(pars, **kwargs)
            self.define_states(
                ss.BoolState('exposed', label='Exposed'),
                ss.FloatArr('ti_exposed', label='Time of exposure'),
            )

        @property
        def infectious(self):
            return self.infected | self.exposed

        def step_state(self):
            super().step_state()
            infected = self.exposed & (self.ti_infected <= self.ti)
            self.exposed[infected] = False
            self.infected[infected] = True

        def step_die(self, uids):
            super().step_die(uids)
            self.exposed[uids] = False

        def set_prognoses(self, uids, sources=None):
            super().set_prognoses(uids, sources)
            ti = self.ti
            self.susceptible[uids] = False
            self.exposed[uids] = True
            self.ti_exposed[uids] = ti
            p = self.pars
            dur_exp = p.dur_exp.rvs(uids)
            self.ti_infected[uids] = ti + dur_exp
            dur_inf = p.dur_inf.rvs(uids)
            will_die = p.p_death.rvs(uids)
            self.ti_recovered[uids[~will_die]] = ti + dur_inf[~will_die]
            self.ti_dead[uids[will_die]] = ti + dur_inf[will_die]

    seir = SEIR(beta=beta, init_prev=init_prev, dur_exp=dur_exp, dur_inf=dur_inf, p_death=p_death)
    sim = ss.Sim(n_agents=n_agents, diseases=seir, networks='random')
    sim.run()
    return sim
```
## starsim_t4.3

### Description
Investigate how varying the exposure (latent) duration affects SEIR epidemic trajectories. Run multiple SEIR simulations with different dur_exp values and compare the cumulative infections and peak number of exposed agents. Longer exposure durations delay the onset of infectiousness and can change the shape of the epidemic curve.

### Background
The exposure (latent) duration in an SEIR model controls how long agents remain in the exposed state before becoming infectious. A longer latent period means there is a greater delay between transmission and infectiousness, which can slow the epidemic and change the peak timing. This is an important parameter for diseases like measles (short latent period) versus tuberculosis (long latent period). To explore this, define a custom SEIR class by subclassing ss.SIR, adding an exposed BoolState and dur_exp parameter.

### Dependencies
- starsim
- numpy

### Function Header
```python
def compare_exposure_durations(dur_exps: list[float], n_agents: int = 5_000, beta: float = 0.1, init_prev: float = 0.05) -> dict[float, dict]:
```

### Docstring
```
Run SEIR simulations with different exposure durations and compare outcomes.

For each dur_exp value, create a custom SEIR model (subclassing ss.SIR with
an exposed compartment) and run a simulation. Collect the cumulative infections
and peak number of exposed agents.

Args:
    dur_exps: List of mean exposure durations to compare (in years).
    n_agents: Number of agents to simulate.
    beta: Probability of transmission between contacts.
    init_prev: Initial proportion of the population that is infected.

Returns:
    Dictionary mapping each dur_exp value to a dict containing:
        - 'cum_infections': cumulative infections at end of simulation
        - 'peak_exposed': maximum number of exposed agents during the simulation
```

### Test Cases

#### Results should contain an entry for each dur_exp value
```python
results = compare_exposure_durations([0.1, 0.5, 2.0])
assert set(results.keys()) == {0.1, 0.5, 2.0}, 'Should have results for all dur_exp values'
```

#### Each result should contain cum_infections and peak_exposed
```python
results = compare_exposure_durations([0.5])
assert 'cum_infections' in results[0.5], 'Should contain cum_infections'
assert 'peak_exposed' in results[0.5], 'Should contain peak_exposed'
```

#### All simulations should produce infections
```python
results = compare_exposure_durations([0.1, 0.5, 2.0])
assert all(v['cum_infections'] > 0 for v in results.values()), 'All simulations should produce infections'
```

#### Peak exposed should be positive for all simulations
```python
results = compare_exposure_durations([0.1, 0.5, 2.0])
assert all(v['peak_exposed'] > 0 for v in results.values()), 'All simulations should have some exposed agents'
```

### Gold Solution
```python
def compare_exposure_durations(dur_exps: list[float], n_agents: int = 5_000, beta: float = 0.1, init_prev: float = 0.05) -> dict[float, dict]:
    import starsim as ss
    import numpy as np

    class SEIR(ss.SIR):
        def __init__(self, pars=None, *args, **kwargs):
            super().__init__()
            self.define_pars(
                dur_exp=ss.lognorm_ex(0.5),
            )
            self.update_pars(pars, **kwargs)
            self.define_states(
                ss.BoolState('exposed', label='Exposed'),
                ss.FloatArr('ti_exposed', label='Time of exposure'),
            )

        @property
        def infectious(self):
            return self.infected | self.exposed

        def step_state(self):
            super().step_state()
            infected = self.exposed & (self.ti_infected <= self.ti)
            self.exposed[infected] = False
            self.infected[infected] = True

        def step_die(self, uids):
            super().step_die(uids)
            self.exposed[uids] = False

        def set_prognoses(self, uids, sources=None):
            super().set_prognoses(uids, sources)
            ti = self.ti
            self.susceptible[uids] = False
            self.exposed[uids] = True
            self.ti_exposed[uids] = ti
            p = self.pars
            dur_exp = p.dur_exp.rvs(uids)
            self.ti_infected[uids] = ti + dur_exp
            dur_inf = p.dur_inf.rvs(uids)
            will_die = p.p_death.rvs(uids)
            self.ti_recovered[uids[~will_die]] = ti + dur_inf[~will_die]
            self.ti_dead[uids[will_die]] = ti + dur_inf[will_die]

    results = {}
    for de in dur_exps:
        seir = SEIR(beta=beta, init_prev=init_prev, dur_exp=de)
        sim = ss.Sim(n_agents=n_agents, diseases=seir, networks='random')
        sim.run()
        results[de] = {
            'cum_infections': float(sim.results.seir.cum_infections[-1]),
            'peak_exposed': float(np.max(sim.results.seir.n_exposed)),
        }
    return results
```
## starsim_t4.4

### Description
Extend the SEIR model to implement SEIRS dynamics, where recovered individuals lose immunity after a period and return to the susceptible state. This enables recurrent epidemic waves as the population cycles through S-E-I-R-S states. Create both the SEIR and SEIRS classes and run a simulation.

### Background
The SEIRS model adds waning immunity to the SEIR framework. After recovering, agents retain immunity for a period (dur_imm) before becoming susceptible again. This allows recurrent epidemics — once enough recovered agents lose immunity, the susceptible pool rebuilds and a new epidemic wave can occur. This is relevant for diseases like influenza or RSV where immunity is temporary. In Starsim, this is implemented by extending the custom SEIR class: add a dur_imm parameter and ti_susceptible FloatArr state, schedule the waning time in set_prognoses (ti_susceptible = ti_recovered + dur_imm), and handle the recovered -> susceptible transition in step_state.

### Dependencies
- starsim

### Function Header
```python
def create_seirs_sim(n_agents: int = 5_000, beta: float = 0.2, init_prev: float = 0.1, dur_exp: float = 0.5, dur_inf: float = 5, dur_imm: float = 2.0, p_death: float = 0.0) -> ss.Sim:
```

### Docstring
```
Create and run a simulation with a custom SEIRS disease model.

First define an SEIR class (subclassing ss.SIR with an exposed compartment),
then define an SEIRS class that extends SEIR by adding waning immunity.
Recovered agents should transition back to susceptible after a period of
dur_imm years. The SEIRS class should:
  - Add a 'dur_imm' parameter (using ss.lognorm_ex distribution)
  - Add a 'ti_susceptible' FloatArr state to schedule waning
  - Override step_state to handle recovered -> susceptible transitions
  - Override set_prognoses to schedule the waning time

Args:
    n_agents: Number of agents to simulate.
    beta: Probability of transmission between contacts.
    init_prev: Initial proportion of the population that is infected.
    dur_exp: Mean duration of the exposed (latent) period in years.
    dur_inf: Duration of infection in years.
    dur_imm: Mean duration of immunity before waning, in years.
    p_death: Probability of death among infected agents.

Returns:
    A Starsim Sim object that has been run to completion with the SEIRS disease.
```

### Test Cases

#### Simulation should have an SEIRS disease
```python
sim = create_seirs_sim()
assert hasattr(sim.diseases, 'seirs'), 'Simulation should have an SEIRS disease'
```

#### Simulation should produce infections
```python
sim = create_seirs_sim()
assert sim.results.seirs.cum_infections[-1] > 0, 'There should be at least some infections'
```

#### SEIRS results should include the exposed compartment
```python
sim = create_seirs_sim()
assert 'n_exposed' in sim.results.seirs, 'SEIRS results should track n_exposed'
```

#### Shorter immunity duration should produce more cumulative infections
```python
short = create_seirs_sim(n_agents=2_000, dur_imm=1.0, beta=0.2, init_prev=0.1, p_death=0.0)
long_ = create_seirs_sim(n_agents=2_000, dur_imm=50.0, beta=0.2, init_prev=0.1, p_death=0.0)
assert short.results.seirs.cum_infections[-1] >= long_.results.seirs.cum_infections[-1], 'Shorter immunity should allow more reinfection'
```

### Gold Solution
```python
def create_seirs_sim(n_agents: int = 5_000, beta: float = 0.2, init_prev: float = 0.1, dur_exp: float = 0.5, dur_inf: float = 5, dur_imm: float = 2.0, p_death: float = 0.0) -> ss.Sim:
    import starsim as ss

    class SEIR(ss.SIR):
        def __init__(self, pars=None, *args, **kwargs):
            super().__init__()
            self.define_pars(
                dur_exp=ss.lognorm_ex(0.5),
            )
            self.update_pars(pars, **kwargs)
            self.define_states(
                ss.BoolState('exposed', label='Exposed'),
                ss.FloatArr('ti_exposed', label='Time of exposure'),
            )

        @property
        def infectious(self):
            return self.infected | self.exposed

        def step_state(self):
            super().step_state()
            infected = self.exposed & (self.ti_infected <= self.ti)
            self.exposed[infected] = False
            self.infected[infected] = True

        def step_die(self, uids):
            super().step_die(uids)
            self.exposed[uids] = False

        def set_prognoses(self, uids, sources=None):
            super().set_prognoses(uids, sources)
            ti = self.ti
            self.susceptible[uids] = False
            self.exposed[uids] = True
            self.ti_exposed[uids] = ti
            p = self.pars
            dur_exp = p.dur_exp.rvs(uids)
            self.ti_infected[uids] = ti + dur_exp
            dur_inf = p.dur_inf.rvs(uids)
            will_die = p.p_death.rvs(uids)
            self.ti_recovered[uids[~will_die]] = ti + dur_inf[~will_die]
            self.ti_dead[uids[will_die]] = ti + dur_inf[will_die]

    class SEIRS(SEIR):
        def __init__(self, pars=None, *args, **kwargs):
            super().__init__()
            self.define_pars(
                dur_imm=ss.lognorm_ex(2.0),
            )
            self.update_pars(pars, **kwargs)
            self.define_states(
                ss.FloatArr('ti_susceptible', label='Time of waning immunity'),
            )

        def step_state(self):
            super().step_state()
            waning = self.recovered & (self.ti_susceptible <= self.ti)
            self.recovered[waning] = False
            self.susceptible[waning] = True

        def set_prognoses(self, uids, sources=None):
            super().set_prognoses(uids, sources)
            p = self.pars
            dur_imm = p.dur_imm.rvs(uids)
            self.ti_susceptible[uids] = self.ti_recovered[uids] + dur_imm

    seirs = SEIRS(beta=beta, init_prev=init_prev, dur_exp=dur_exp, dur_inf=dur_inf, dur_imm=dur_imm, p_death=p_death)
    sim = ss.Sim(n_agents=n_agents, diseases=seirs, networks='random')
    sim.run()
    return sim
```
