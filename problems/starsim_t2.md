# starsim_t2

## starsim_t2.1

### Description
Create and run an SIR simulation using Starsim's component-based approach. Instead of passing a parameters dictionary, instantiate individual component objects (ss.People, ss.RandomNet, ss.SIR) and pass them directly to ss.Sim. This approach provides greater flexibility for configuring and reusing model components.

### Background
Starsim supports two ways of configuring simulations. The dictionary approach bundles all parameters into a single dict, while the component-based approach creates individual objects (People, Networks, Diseases) that are passed to the Sim constructor. The component approach is preferred for complex models because each component can be configured independently and reused across simulations.

### Dependencies
- starsim

### Function Header
```python
def create_component_sim(n_agents: int = 5_000, n_contacts: int = 4, init_prev: float = 0.1, beta: float = 0.1) -> ss.Sim:
```

### Docstring
```
Create and run an SIR simulation using Starsim's component-based approach.

Instead of using a parameters dictionary, create individual component objects
(ss.People, ss.RandomNet, ss.SIR) and pass them to ss.Sim.

Args:
    n_agents: Number of agents to simulate.
    n_contacts: Average number of contacts per agent in the random network.
    init_prev: Initial proportion of the population that is infected.
    beta: Probability of transmission between contacts.

Returns:
    A Starsim Sim object that has been run to completion.
```

### Test Cases

#### Simulation should use an SIR disease via component objects
```python
sim = create_component_sim()
assert hasattr(sim.diseases, 'sir'), 'Simulation should have an SIR disease'
```

#### Disease should be instantiated as an ss.SIR object
```python
import starsim as ss
sim = create_component_sim()
disease = list(sim.diseases.values())[0]
assert isinstance(disease, ss.SIR), 'Disease should be an ss.SIR instance'
```

#### Network should be instantiated as an ss.RandomNet object
```python
import starsim as ss
sim = create_component_sim()
network = list(sim.networks.values())[0]
assert isinstance(network, ss.RandomNet), 'Network should be an ss.RandomNet instance'
```

#### Simulation should produce infections
```python
sim = create_component_sim()
assert sim.results.sir.cum_infections[-1] > 0, 'There should be at least some infections'
```

#### Population size should match n_agents parameter
```python
sim = create_component_sim(n_agents=1_000)
assert sim.pars.n_agents == 1_000, 'Population size should match the n_agents parameter'
```

### Gold Solution
```python
def create_component_sim(n_agents: int = 5_000, n_contacts: int = 4, init_prev: float = 0.1, beta: float = 0.1) -> ss.Sim:
    import starsim as ss
    people = ss.People(n_agents=n_agents)
    network = ss.RandomNet(n_contacts=n_contacts)
    sir = ss.SIR(init_prev=init_prev, beta=beta)
    sim = ss.Sim(people=people, diseases=sir, networks=network)
    sim.run()
    return sim
```
## starsim_t2.2

### Description
Create a simulation with heterogeneous contact patterns by using a Poisson-distributed number of contacts instead of a fixed value. In real populations, the number of contacts varies from person to person. Starsim's distribution objects (e.g., ss.poisson) let you model this variation.

### Background
In real populations, the number of contacts varies across individuals. Some people have many contacts while others have few. This heterogeneity affects disease spread because highly connected individuals can act as super-spreaders. Starsim supports this via distribution objects like ss.poisson(lam), which draws a different number of contacts for each agent from a Poisson distribution with the given mean.

### Dependencies
- starsim

### Function Header
```python
def create_heterogeneous_sim(n_agents: int = 5_000, mean_contacts: int = 4, init_prev: float = 0.1, beta: float = 0.1) -> ss.Sim:
```

### Docstring
```
Create and run an SIR simulation with heterogeneous (Poisson-distributed) contacts.

Args:
    n_agents: Number of agents to simulate.
    mean_contacts: Mean number of contacts per agent (lambda for Poisson distribution).
    init_prev: Initial proportion of the population that is infected.
    beta: Probability of transmission between contacts.

Returns:
    A Starsim Sim object that has been run to completion.
```

### Test Cases

#### Simulation should have an SIR disease
```python
sim = create_heterogeneous_sim()
assert hasattr(sim.diseases, 'sir'), 'Simulation should have an SIR disease'
```

#### Network should be a RandomNet
```python
import starsim as ss
sim = create_heterogeneous_sim()
network = list(sim.networks.values())[0]
assert isinstance(network, ss.RandomNet), 'Network should be a RandomNet'
```

#### Simulation should produce infections
```python
sim = create_heterogeneous_sim()
assert sim.results.sir.cum_infections[-1] > 0, 'There should be at least some infections'
```

#### Population size should match n_agents parameter
```python
sim = create_heterogeneous_sim(n_agents=1_000)
assert sim.pars.n_agents == 1_000, 'Population size should match n_agents'
```

### Gold Solution
```python
def create_heterogeneous_sim(n_agents: int = 5_000, mean_contacts: int = 4, init_prev: float = 0.1, beta: float = 0.1) -> ss.Sim:
    import starsim as ss
    people = ss.People(n_agents=n_agents)
    network = ss.RandomNet(n_contacts=ss.poisson(mean_contacts))
    sir = ss.SIR(init_prev=init_prev, beta=beta)
    sim = ss.Sim(people=people, diseases=sir, networks=network)
    sim.run()
    return sim
```
## starsim_t2.3

### Description
Model an outbreak of an SIR-like disease in a refugee camp of 2,000 people over 1 year with daily timesteps. Use the component-based approach with appropriate time units (ss.days for duration of infection, ss.perday for beta). Return the cumulative number of infections at the end of the simulation.

### Background
When modeling outbreaks at daily resolution, parameter units must match the timestep. Starsim provides unit-aware helpers: ss.days(n) specifies a duration in days, and ss.perday(rate) specifies a per-day rate. These ensure correct behavior regardless of the simulation's dt setting. For a refugee camp scenario, daily timesteps capture rapid outbreak dynamics that annual timesteps would miss.

### Dependencies
- starsim

### Function Header
```python
def refugee_camp_outbreak(n_agents: int = 2_000, n_contacts: int = 4, init_prev: float = 0.001, beta: float = 0.02, dur_inf: int = 14) -> float:
```

### Docstring
```
Model an SIR outbreak in a refugee camp and return cumulative infections.

Configure a daily-timestep simulation running for 1 year starting from
2025-01-01. Use ss.days() for the duration of infection and ss.perday()
for the transmission rate to ensure correct unit handling with daily
timesteps.

Args:
    n_agents: Number of people in the refugee camp.
    n_contacts: Average number of contacts per person.
    init_prev: Initial proportion of the population that is infected.
    beta: Per-day transmission probability.
    dur_inf: Duration of infection in days.

Returns:
    Cumulative number of infections at the end of the 1-year simulation.
```

### Test Cases

#### Should return a positive number of cumulative infections
```python
result = refugee_camp_outbreak()
assert result > 0, 'Should have at least some infections'
```

#### Return value should be a float
```python
result = refugee_camp_outbreak()
assert isinstance(result, float), 'Should return a float'
```

#### Cumulative infections should not exceed population size
```python
n = 2_000
result = refugee_camp_outbreak(n_agents=n)
assert result <= n, 'Cumulative infections should not exceed population size'
```

#### Higher beta should produce more infections
```python
low = refugee_camp_outbreak(n_agents=2_000, beta=0.005)
high = refugee_camp_outbreak(n_agents=2_000, beta=0.05)
assert high > low, 'Higher beta should produce more infections'
```

### Gold Solution
```python
def refugee_camp_outbreak(n_agents: int = 2_000, n_contacts: int = 4, init_prev: float = 0.001, beta: float = 0.02, dur_inf: int = 14) -> float:
    import starsim as ss
    people = ss.People(n_agents=n_agents)
    network = ss.RandomNet(n_contacts=n_contacts)
    sir = ss.SIR(dur_inf=ss.days(dur_inf), beta=ss.perday(beta), init_prev=init_prev)
    sim = ss.Sim(people=people, diseases=sir, networks=network, start='2025-01-01', dur=365, dt='day')
    sim.run()
    return float(sim.results.sir.cum_infections[-1])
```
## starsim_t2.4

### Description
Explore how different epidemic drivers affect outbreak size. Run SIR simulations varying beta (transmissibility), n_contacts (contact rate), and dur_inf (duration of infection) to understand how each factor independently influences the cumulative number of infections. Return a dictionary of results for each parameter sweep.

### Background
The basic reproduction number R0 — the average number of secondary infections from a single case in a fully susceptible population — depends on the transmissibility (beta), contact rate (c), and duration of infection (D): R0 = beta * c * D. By sweeping each parameter independently while holding the others fixed, you can see how each factor drives epidemic size. This is a fundamental exercise in understanding infectious disease dynamics.

### Dependencies
- starsim

### Function Header
```python
def explore_epidemic_drivers(betas: list[float] = [0.01, 0.05, 0.10], n_contacts_list: list[int] = [2, 4, 8], dur_infs: list[int] = [5, 10, 20], n_agents: int = 5_000) -> dict[str, dict]:
```

### Docstring
```
Run SIR simulations varying key epidemic parameters and compare outcomes.

For each parameter sweep, hold all other parameters at their defaults
(beta=0.05, n_contacts=4, dur_inf=10) and vary only the target parameter.

Args:
    betas: List of transmission probabilities to sweep.
    n_contacts_list: List of contact rates to sweep.
    dur_infs: List of infection durations (in days) to sweep.
    n_agents: Number of agents per simulation.

Returns:
    Dictionary with three keys:
        - 'beta': dict mapping each beta value to cumulative infections
        - 'n_contacts': dict mapping each n_contacts value to cumulative infections
        - 'dur_inf': dict mapping each dur_inf value to cumulative infections
```

### Test Cases

#### Result should contain beta, n_contacts, and dur_inf keys
```python
results = explore_epidemic_drivers()
assert set(results.keys()) == {'beta', 'n_contacts', 'dur_inf'}, 'Should have beta, n_contacts, and dur_inf keys'
```

#### Beta sweep should have correct keys
```python
results = explore_epidemic_drivers(betas=[0.01, 0.10])
assert set(results['beta'].keys()) == {0.01, 0.10}, 'Beta sweep should have entries for each beta value'
```

#### Contact sweep should have correct keys
```python
results = explore_epidemic_drivers(n_contacts_list=[2, 8])
assert set(results['n_contacts'].keys()) == {2, 8}, 'Contact sweep should have entries for each n_contacts value'
```

#### Duration sweep should have correct keys
```python
results = explore_epidemic_drivers(dur_infs=[5, 20])
assert set(results['dur_inf'].keys()) == {5, 20}, 'Duration sweep should have entries for each dur_inf value'
```

#### Higher beta should generally produce more infections
```python
results = explore_epidemic_drivers(betas=[0.01, 0.10], n_agents=5_000)
assert results['beta'][0.10] > results['beta'][0.01], 'Higher beta should produce more infections'
```

#### More contacts should generally produce more infections
```python
results = explore_epidemic_drivers(n_contacts_list=[2, 8], n_agents=5_000)
assert results['n_contacts'][8] > results['n_contacts'][2], 'More contacts should produce more infections'
```

#### All infection counts should be non-negative
```python
results = explore_epidemic_drivers()
for sweep_name, sweep in results.items():
    for param_val, count in sweep.items():
        assert count >= 0, f'{sweep_name}={param_val} should have non-negative infections'
```

### Gold Solution
```python
def explore_epidemic_drivers(betas: list[float] = [0.01, 0.05, 0.10], n_contacts_list: list[int] = [2, 4, 8], dur_infs: list[int] = [5, 10, 20], n_agents: int = 5_000) -> dict[str, dict]:
    import starsim as ss
    results = {'beta': {}, 'n_contacts': {}, 'dur_inf': {}}
    # Sweep beta
    for beta in betas:
        sir = ss.SIR(init_prev=0.01, beta=beta, dur_inf=10)
        sim = ss.Sim(people=ss.People(n_agents=n_agents), diseases=sir, networks=ss.RandomNet(n_contacts=4))
        sim.run()
        results['beta'][beta] = float(sim.results.sir.cum_infections[-1])
    # Sweep n_contacts
    for nc in n_contacts_list:
        sir = ss.SIR(init_prev=0.01, beta=0.05, dur_inf=10)
        sim = ss.Sim(people=ss.People(n_agents=n_agents), diseases=sir, networks=ss.RandomNet(n_contacts=nc))
        sim.run()
        results['n_contacts'][nc] = float(sim.results.sir.cum_infections[-1])
    # Sweep dur_inf
    for di in dur_infs:
        sir = ss.SIR(init_prev=0.01, beta=0.05, dur_inf=di)
        sim = ss.Sim(people=ss.People(n_agents=n_agents), diseases=sir, networks=ss.RandomNet(n_contacts=4))
        sim.run()
        results['dur_inf'][di] = float(sim.results.sir.cum_infections[-1])
    return results
```
