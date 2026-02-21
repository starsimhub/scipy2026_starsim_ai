# starsim_t3

## starsim_t3.1

### Description
Create and run an SIR simulation that includes vital dynamics (births and deaths) using the parameters dictionary approach. Add demographic rates alongside disease and network parameters so that the population size changes over time due to births and deaths, and agents age during the simulation.

### Background
In basic epidemic models, the population is often fixed — no one is born or dies from non-disease causes. Adding demographics (births and deaths) makes the model more realistic for longer-term projections. In Starsim, specifying birth_rate and death_rate in the parameters dictionary automatically creates Births and Deaths demographic modules. When demographics modules are present, agents also age over time (use_aging becomes True).

### Dependencies
- starsim

### Function Header
```python
def create_sir_with_demographics(n_agents: int = 5_000, birth_rate: float = 20, death_rate: float = 15, beta: float = 0.05, init_prev: float = 0.01) -> ss.Sim:
```

### Docstring
```
Create and run an SIR simulation with birth and death dynamics.

Use a parameters dictionary that includes birth_rate, death_rate,
a random contact network, and SIR disease. The simulation should
run from 2020 to 2040.

Args:
    n_agents: Number of agents to simulate.
    birth_rate: Crude birth rate (per 1000 people per year).
    death_rate: Crude death rate (per 1000 people per year).
    beta: Probability of transmission between contacts.
    init_prev: Initial proportion of the population that is infected.

Returns:
    A Starsim Sim object that has been run to completion.
```

### Test Cases

#### Simulation should have births and deaths demographic modules
```python
sim = create_sir_with_demographics()
assert hasattr(sim.demographics, 'births'), 'Simulation should have a births demographic module'
assert hasattr(sim.demographics, 'deaths'), 'Simulation should have a deaths demographic module'
```

#### Simulation should have an SIR disease
```python
sim = create_sir_with_demographics()
assert hasattr(sim.diseases, 'sir'), 'Simulation should have an SIR disease'
```

#### Agents should age during the simulation
```python
sim = create_sir_with_demographics()
assert sim.pars.use_aging is True, 'Agents should age when demographics are included'
```

#### Simulation should produce infections
```python
sim = create_sir_with_demographics()
assert sim.results.sir.cum_infections[-1] > 0, 'There should be at least some infections'
```

#### Results should include birth and death tracking
```python
sim = create_sir_with_demographics()
assert 'births' in sim.results, 'Results should track births'
assert 'new_deaths' in sim.results, 'Results should track deaths'
```

### Gold Solution
```python
def create_sir_with_demographics(n_agents: int = 5_000, birth_rate: float = 20, death_rate: float = 15, beta: float = 0.05, init_prev: float = 0.01) -> ss.Sim:
    import starsim as ss
    pars = dict(
        n_agents=n_agents,
        birth_rate=birth_rate,
        death_rate=death_rate,
        networks='random',
        diseases=dict(type='sir', init_prev=init_prev, beta=beta),
        start=2020,
        stop=2040,
    )
    sim = ss.Sim(pars)
    sim.run()
    return sim
```
## starsim_t3.2

### Description
Create a simulation with demographics using the component-based approach. Instantiate ss.Births and ss.Deaths objects explicitly and pass them via the demographics parameter, along with component-based disease and network objects. This approach provides more flexibility for configuring demographic modules.

### Background
Just as diseases and networks can be configured using component objects (Tutorial 2), demographic modules can also be created as explicit objects. ss.Births(birth_rate=...) and ss.Deaths(death_rate=...) are passed as a list to the demographics parameter of ss.Sim. This is preferred for complex models where you need fine-grained control over each module.

### Dependencies
- starsim

### Function Header
```python
def create_component_demographics(n_agents: int = 5_000, birth_rate: float = 20, death_rate: float = 15, beta: float = 0.05, init_prev: float = 0.01) -> ss.Sim:
```

### Docstring
```
Create and run an SIR simulation with demographics using the component-based approach.

Instantiate ss.Births, ss.Deaths, ss.SIR, ss.RandomNet, and ss.People
objects explicitly and pass them to ss.Sim. The simulation should run
from 2020 to 2040.

Args:
    n_agents: Number of agents to simulate.
    birth_rate: Crude birth rate (per 1000 people per year).
    death_rate: Crude death rate (per 1000 people per year).
    beta: Probability of transmission between contacts.
    init_prev: Initial proportion of the population that is infected.

Returns:
    A Starsim Sim object that has been run to completion.
```

### Test Cases

#### Births module should be an ss.Births instance
```python
import starsim as ss
sim = create_component_demographics()
births_mod = list(sim.demographics.values())[0]
assert isinstance(births_mod, ss.Births), 'Births module should be an ss.Births instance'
```

#### Deaths module should be an ss.Deaths instance
```python
import starsim as ss
sim = create_component_demographics()
deaths_mod = list(sim.demographics.values())[1]
assert isinstance(deaths_mod, ss.Deaths), 'Deaths module should be an ss.Deaths instance'
```

#### Disease should be an ss.SIR instance
```python
import starsim as ss
sim = create_component_demographics()
disease = list(sim.diseases.values())[0]
assert isinstance(disease, ss.SIR), 'Disease should be an ss.SIR instance'
```

#### Population size should change due to demographics
```python
sim = create_component_demographics()
initial = sim.results.n_alive[0]
final = sim.results.n_alive[-1]
assert initial != final, 'Population should change over time with demographics'
```

### Gold Solution
```python
def create_component_demographics(n_agents: int = 5_000, birth_rate: float = 20, death_rate: float = 15, beta: float = 0.05, init_prev: float = 0.01) -> ss.Sim:
    import starsim as ss
    people = ss.People(n_agents=n_agents)
    births = ss.Births(birth_rate=birth_rate)
    deaths = ss.Deaths(death_rate=death_rate)
    sir = ss.SIR(init_prev=init_prev, beta=beta)
    network = ss.RandomNet()
    sim = ss.Sim(people=people, diseases=sir, networks=network, demographics=[births, deaths], start=2020, stop=2040)
    sim.run()
    return sim
```
## starsim_t3.3

### Description
Project the population of Niger from 2020 to 2040. Niger has a crude birth rate of 45 per 1000 and a crude death rate of 9 per 1000. Assuming these rates stay constant and starting with a total population of 24 million, use Starsim's total_pop parameter to scale the simulation results and return the projected population in millions.

### Background
Starsim's total_pop parameter enables statistical scaling: the simulation runs with a manageable number of agents but reports results scaled to represent a much larger population. This is useful for national-level projections where simulating every individual would be computationally prohibitive. With a net growth rate of 36 per 1000 (birth rate minus death rate), Niger's population grows rapidly.

### Dependencies
- starsim

### Function Header
```python
def project_niger_population(total_pop: float = 24e6, birth_rate: float = 45, death_rate: float = 9, start: int = 2020, stop: int = 2040) -> float:
```

### Docstring
```
Project Niger's population using Starsim demographic modeling.

Create a simulation with the given birth and death rates. Use the
total_pop parameter to scale the simulation (which runs with a smaller
number of agents) to represent the full population. Do not include
any diseases in the model.

Args:
    total_pop: Total population to scale results to.
    birth_rate: Crude birth rate (per 1000 people per year).
    death_rate: Crude death rate (per 1000 people per year).
    start: Start year of the simulation.
    stop: End year of the simulation.

Returns:
    Projected population at the end of the simulation, in millions
    (e.g., 49.5 means 49.5 million).
```

### Test Cases

#### Projected population should be approximately 49-51 million
```python
result = project_niger_population()
assert 45 < result < 55, f'Population should be roughly 49-51 million, got {result:.1f}'
```

#### Return value should be a float representing millions
```python
result = project_niger_population()
assert isinstance(result, float), 'Should return a float'
```

#### Higher birth rate should produce larger population
```python
low = project_niger_population(birth_rate=20)
high = project_niger_population(birth_rate=45)
assert high > low, 'Higher birth rate should produce a larger population'
```

#### Population should grow when birth rate exceeds death rate
```python
result = project_niger_population()
assert result > 24, 'Population should grow beyond the initial 24 million'
```

### Gold Solution
```python
def project_niger_population(total_pop: float = 24e6, birth_rate: float = 45, death_rate: float = 9, start: int = 2020, stop: int = 2040) -> float:
    import starsim as ss
    pars = dict(
        start=start,
        stop=stop,
        total_pop=total_pop,
        birth_rate=birth_rate,
        death_rate=death_rate,
    )
    sim = ss.Sim(pars)
    sim.run()
    return float(sim.results.n_alive[-1] / 1e6)
```
## starsim_t3.4

### Description
Compare how disease dynamics differ with and without demographic processes. Run two SIR simulations over a 20-year period — one without demographics (fixed population) and one with births and deaths — and return key outcome metrics from each. This illustrates how population turnover affects long-term epidemic dynamics.

### Background
Without demographics, a population is closed — no new susceptible individuals enter (via birth) and no one leaves (via non-disease death). In an SIR model, this means the epidemic burns through the susceptible pool and dies out permanently. With demographics, new births continuously replenish the susceptible pool, which can sustain or reignite transmission over longer time horizons. This is a key consideration when choosing whether to include demographics in a model.

### Dependencies
- starsim

### Function Header
```python
def compare_demographics_impact(n_agents: int = 5_000, birth_rate: float = 20, death_rate: float = 10, beta: float = 0.05, init_prev: float = 0.01) -> dict[str, dict]:
```

### Docstring
```
Compare SIR dynamics with and without demographic processes.

Run two simulations from 2020 to 2040:
1. 'no_demographics': SIR with a random network, no births/deaths
2. 'with_demographics': SIR with a random network plus births and deaths

Args:
    n_agents: Number of agents to simulate.
    birth_rate: Crude birth rate (per 1000 per year), used only in the demographics sim.
    death_rate: Crude death rate (per 1000 per year), used only in the demographics sim.
    beta: Probability of transmission between contacts.
    init_prev: Initial proportion of the population that is infected.

Returns:
    Dictionary with two keys ('no_demographics', 'with_demographics'),
    each mapping to a dict containing:
        - 'final_pop': number of living agents at the end of the simulation
        - 'cum_infections': cumulative SIR infections at end of simulation
```

### Test Cases

#### Result should have both scenario keys
```python
results = compare_demographics_impact()
assert set(results.keys()) == {'no_demographics', 'with_demographics'}, 'Should have both scenario keys'
```

#### Each scenario should have final_pop and cum_infections
```python
results = compare_demographics_impact()
for key in ['no_demographics', 'with_demographics']:
    assert 'final_pop' in results[key], f'{key} should have final_pop'
    assert 'cum_infections' in results[key], f'{key} should have cum_infections'
```

#### Population should change with demographics but stay roughly constant without
```python
results = compare_demographics_impact(n_agents=5_000, birth_rate=30, death_rate=10)
no_demog_pop = results['no_demographics']['final_pop']
with_demog_pop = results['with_demographics']['final_pop']
assert with_demog_pop > no_demog_pop, 'Population with net-positive demographics should be larger than without'
```

#### Both scenarios should produce infections
```python
results = compare_demographics_impact()
assert results['no_demographics']['cum_infections'] > 0, 'No-demographics scenario should have infections'
assert results['with_demographics']['cum_infections'] > 0, 'With-demographics scenario should have infections'
```

### Gold Solution
```python
def compare_demographics_impact(n_agents: int = 5_000, birth_rate: float = 20, death_rate: float = 10, beta: float = 0.05, init_prev: float = 0.01) -> dict[str, dict]:
    import starsim as ss
    results = {}
    # Without demographics
    sim_no = ss.Sim(
        n_agents=n_agents,
        diseases=dict(type='sir', init_prev=init_prev, beta=beta),
        networks='random',
        start=2020,
        stop=2040,
    )
    sim_no.run()
    results['no_demographics'] = {
        'final_pop': float(sim_no.results.n_alive[-1]),
        'cum_infections': float(sim_no.results.sir.cum_infections[-1]),
    }
    # With demographics
    sim_yes = ss.Sim(
        n_agents=n_agents,
        diseases=dict(type='sir', init_prev=init_prev, beta=beta),
        networks='random',
        birth_rate=birth_rate,
        death_rate=death_rate,
        start=2020,
        stop=2040,
    )
    sim_yes.run()
    results['with_demographics'] = {
        'final_pop': float(sim_yes.results.n_alive[-1]),
        'cum_infections': float(sim_yes.results.sir.cum_infections[-1]),
    }
    return results
```
