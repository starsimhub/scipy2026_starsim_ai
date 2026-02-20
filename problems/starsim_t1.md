# starsim_t1

## starsim_t1.1

### Description
Create and run a basic SIR (susceptible-infectious-recovered) simulation using Starsim. The simulation should use a random contact network and return the completed simulation object.

### Background
The SIR (susceptible-infectious-recovered) model is a fundamental compartmental model in epidemiology. Individuals start as susceptible (S), become infected (I) upon contact with an infectious individual, and eventually recover (R) with permanent immunity. In Starsim, disease dynamics are configured via the 'diseases' parameter, and agent interactions are governed by contact networks.

### Dependencies
- starsim

### Function Header
```python
def create_sir_sim(n_agents: int = 10_000, n_contacts: int = 10, init_prev: float = 0.01, beta: float = 0.05) -> ss.Sim:
```

### Docstring
```
Create and run a basic SIR disease simulation using Starsim.

Args:
    n_agents: Number of agents to simulate.
    n_contacts: Average number of contacts per agent in the random network.
    init_prev: Initial proportion of the population that is infected.
    beta: Probability of transmission between contacts.

Returns:
    A Starsim Sim object that has been run to completion.
```

### Test Cases

#### Simulation should have an SIR disease
```python
sim = create_sir_sim()
assert hasattr(sim.diseases, 'sir'), 'Simulation should have an SIR disease'
```

#### Simulation should have results after running
```python
sim = create_sir_sim()
assert sim.results.sir.cum_infections[-1] > 0, 'There should be at least some infections'
```

#### Population size should match n_agents parameter
```python
sim = create_sir_sim(n_agents=500)
assert sim.pars.n_agents == 500, 'Population size should match the n_agents parameter'
```

#### SIR compartments should be present in results
```python
sim = create_sir_sim()
assert 'n_susceptible' in sim.results.sir, 'Results should contain n_susceptible'
assert 'n_infected' in sim.results.sir, 'Results should contain n_infected'
assert 'n_recovered' in sim.results.sir, 'Results should contain n_recovered'
```

### Gold Solution
```python
def create_sir_sim(n_agents: int = 10_000, n_contacts: int = 10, init_prev: float = 0.01, beta: float = 0.05) -> ss.Sim:
    import starsim as ss
    pars = dict(
        n_agents=n_agents,
        networks=dict(type='random', n_contacts=n_contacts),
        diseases=dict(type='sir', init_prev=init_prev, beta=beta),
    )
    sim = ss.Sim(pars)
    sim.run()
    return sim
```
## starsim_t1.2

### Description
Modify the basic simulation to model SIS (susceptible-infectious-susceptible) dynamics instead of SIR. In an SIS model, individuals do not gain permanent immunity after infection — they return to the susceptible state and can be reinfected.

### Background
The SIS (susceptible-infectious-susceptible) model differs from SIR in that recovered individuals return to the susceptible compartment instead of gaining permanent immunity. This is appropriate for diseases where immunity is temporary or nonexistent (e.g., bacterial infections, some STIs). In Starsim, switching between SIR and SIS requires changing the disease type parameter.

### Dependencies
- starsim

### Function Header
```python
def create_sis_sim(n_agents: int = 10_000, n_contacts: int = 10, init_prev: float = 0.01, beta: float = 0.05) -> ss.Sim:
```

### Docstring
```
Create and run an SIS disease simulation using Starsim.

Args:
    n_agents: Number of agents to simulate.
    n_contacts: Average number of contacts per agent in the random network.
    init_prev: Initial proportion of the population that is infected.
    beta: Probability of transmission between contacts.

Returns:
    A Starsim Sim object that has been run to completion with an SIS disease.
```

### Test Cases

#### Simulation should have an SIS disease (not SIR)
```python
sim = create_sis_sim()
assert hasattr(sim.diseases, 'sis'), 'Simulation should have an SIS disease'
assert not hasattr(sim.diseases, 'sir'), 'Simulation should NOT have an SIR disease'
```

#### SIS results should not have a recovered compartment
```python
sim = create_sis_sim()
assert 'n_recovered' not in sim.results.sis, 'SIS model should not have a recovered compartment'
```

#### SIS model should have cumulative infections
```python
sim = create_sis_sim()
assert sim.results.sis.cum_infections[-1] > 0, 'There should be infections in the SIS model'
```

### Gold Solution
```python
def create_sis_sim(n_agents: int = 10_000, n_contacts: int = 10, init_prev: float = 0.01, beta: float = 0.05) -> ss.Sim:
    import starsim as ss
    pars = dict(
        n_agents=n_agents,
        networks=dict(type='random', n_contacts=n_contacts),
        diseases=dict(type='sis', init_prev=init_prev, beta=beta),
    )
    sim = ss.Sim(pars)
    sim.run()
    return sim
```
## starsim_t1.3

### Description
Explore how the transmission rate (beta) affects disease dynamics. Run multiple SIR simulations with different beta values and compare the cumulative number of infections. Higher beta values should lead to faster, larger epidemics.

### Background
The transmission rate beta is a key parameter in disease modeling that controls how easily the disease spreads between contacts. Higher beta values mean each contact between a susceptible and infectious individual is more likely to result in transmission. This directly affects the basic reproduction number (R0) and the final size of the epidemic.

### Dependencies
- starsim

### Function Header
```python
def compare_beta(betas: list[float], n_agents: int = 10_000, n_contacts: int = 10, init_prev: float = 0.01) -> dict[float, float]:
```

### Docstring
```
Run SIR simulations with different transmission rates and compare outcomes.

Args:
    betas: List of transmission probabilities to compare (e.g., [0.02, 0.05, 0.10]).
    n_agents: Number of agents to simulate.
    n_contacts: Average number of contacts per agent.
    init_prev: Initial proportion infected.

Returns:
    Dictionary mapping each beta value to the cumulative number of infections
    at the end of the simulation.
```

### Test Cases

#### Results should contain an entry for each beta value
```python
results = compare_beta([0.02, 0.05, 0.10])
assert set(results.keys()) == {0.02, 0.05, 0.10}, 'Should have results for all beta values'
```

#### Higher beta should generally produce more cumulative infections
```python
results = compare_beta([0.01, 0.10], n_agents=10_000)
assert results[0.10] > results[0.01], 'Higher beta should produce more infections'
```

#### All infection counts should be positive
```python
results = compare_beta([0.02, 0.05, 0.10])
assert all(v > 0 for v in results.values()), 'All simulations should produce some infections'
```

### Gold Solution
```python
def compare_beta(betas: list[float], n_agents: int = 10_000, n_contacts: int = 10, init_prev: float = 0.01) -> dict[float, float]:
    import starsim as ss
    results = {}
    for beta in betas:
        pars = dict(
            n_agents=n_agents,
            networks=dict(type='random', n_contacts=n_contacts),
            diseases=dict(type='sir', init_prev=init_prev, beta=beta),
        )
        sim = ss.Sim(pars)
        sim.run()
        results[beta] = float(sim.results.sir.cum_infections[-1])
    return results
```
## starsim_t1.4

### Description
Investigate how population size affects simulation results. Run SIR simulations with different numbers of agents and compare the results. Smaller populations produce noisier (less smooth) epidemic curves due to greater stochastic variation.

### Background
Agent-based models like Starsim are stochastic — each simulation run produces slightly different results due to random variation. With large populations, individual random events average out and curves appear smooth. With small populations, random effects are more pronounced, leading to noisier curves. This is an important consideration when choosing population size for modeling studies.

### Dependencies
- starsim

### Function Header
```python
def compare_population_sizes(n_agents_list: list[int], n_contacts: int = 10, init_prev: float = 0.01, beta: float = 0.05) -> dict[int, dict]:
```

### Docstring
```
Run SIR simulations with different population sizes and compare outcomes.

Args:
    n_agents_list: List of population sizes to compare (e.g., [200, 10_000]).
    n_contacts: Average number of contacts per agent.
    init_prev: Initial proportion infected.
    beta: Probability of transmission between contacts.

Returns:
    Dictionary mapping each population size to a dict containing:
        - 'cum_infections': cumulative infections at end of simulation
        - 'peak_prevalence': maximum prevalence observed during the simulation
```

### Test Cases

#### Results should contain an entry for each population size
```python
results = compare_population_sizes([200, 5_000])
assert set(results.keys()) == {200, 5_000}, 'Should have results for all population sizes'
```

#### Each result should contain cum_infections and peak_prevalence
```python
results = compare_population_sizes([1_000])
assert 'cum_infections' in results[1_000], 'Should contain cum_infections'
assert 'peak_prevalence' in results[1_000], 'Should contain peak_prevalence'
```

#### Cumulative infections should be positive for all population sizes
```python
results = compare_population_sizes([200, 5_000])
assert all(r['cum_infections'] > 0 for r in results.values()), 'All simulations should produce infections'
```

#### Peak prevalence should be between 0 and 1
```python
results = compare_population_sizes([1_000])
assert 0 < results[1_000]['peak_prevalence'] <= 1.0, 'Peak prevalence should be a valid proportion'
```

### Gold Solution
```python
def compare_population_sizes(n_agents_list: list[int], n_contacts: int = 10, init_prev: float = 0.01, beta: float = 0.05) -> dict[int, dict]:
    import starsim as ss
    import numpy as np
    results = {}
    for n_agents in n_agents_list:
        pars = dict(
            n_agents=n_agents,
            networks=dict(type='random', n_contacts=n_contacts),
            diseases=dict(type='sir', init_prev=init_prev, beta=beta),
        )
        sim = ss.Sim(pars)
        sim.run()
        prevalence = sim.results.sir.prevalence
        results[n_agents] = {
            'cum_infections': float(sim.results.sir.cum_infections[-1]),
            'peak_prevalence': float(np.max(prevalence)),
        }
    return results
```
